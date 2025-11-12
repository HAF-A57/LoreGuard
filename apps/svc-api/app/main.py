"""
LoreGuard API Service
Main FastAPI application entry point
"""

import sys
import os
from pathlib import Path

# CRITICAL: Prevent this module from executing when imported from assistant service
# The API service runs from /app/app/main.py, but assistant imports from /app/svc-api-app/main.py
_this_file = Path(__file__).resolve()
_this_file_str = str(_this_file)

# Check if this is being imported as 'main' (not 'app.main' or 'models.main' etc.)
# Only block if imported as top-level 'main' from /app/svc-api-app
_is_top_level_main_import = __name__ == 'main'
_is_from_svc_api_app = '/svc-api-app/main.py' in _this_file_str

# Also check environment variable
_service_name = os.getenv('SERVICE_NAME', '')
_is_assistant_context = 'assistant' in _service_name.lower()

# Only block if: (1) imported as top-level 'main' AND from svc-api-app, OR (2) in assistant context
# Don't block if imported as 'app.main' or any other qualified import
if _is_top_level_main_import and _is_from_svc_api_app:
    # This is being imported as 'main' from svc-api-app - block it
    import types
    _dummy = types.ModuleType(__name__)
    _dummy.__file__ = _this_file_str
    sys.modules[__name__] = _dummy
    _skip_execution = True
elif _is_assistant_context and _is_from_svc_api_app:
    # In assistant context and from svc-api-app - also block
    import types
    _dummy = types.ModuleType(__name__)
    _dummy.__file__ = _this_file_str
    sys.modules[__name__] = _dummy
    _skip_execution = True
else:
    _skip_execution = False

# Only execute API service code if we're in the right context
if not _skip_execution:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.trustedhost import TrustedHostMiddleware
    from fastapi.responses import JSONResponse
    from contextlib import asynccontextmanager
    import logging
    import asyncio

    # Add the app directory to Python path
    sys.path.append(str(Path(__file__).parent))

    from core.config import settings
    from db.database import engine, create_tables
    from api.v1.api import api_router

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Application lifespan manager"""
        # Startup
        logger.info("Starting LoreGuard API service...")
        
        # Create database tables
        await create_tables()
        logger.info("Database tables created/verified")
        
        # Initialize database with default data (including default rubric)
        from db.database import init_db
        await init_db()
        logger.info("Database initialized with default data")
        
        # Start background job health checker for automatic job monitoring
        from services.job_health_checker import JobHealthChecker
        health_checker = JobHealthChecker(check_interval_seconds=60)
        app.state.job_health_checker = health_checker
        asyncio.create_task(health_checker.start_monitoring())
        logger.info("Job health checker started")
        
        # Start source scheduler for automatic crawl scheduling
        from services.scheduler_service import SchedulerService
        scheduler = SchedulerService(check_interval_seconds=60)
        app.state.scheduler = scheduler
        asyncio.create_task(scheduler.start_scheduler())
        logger.info("Source scheduler started")
        
        yield
        
        # Shutdown
        logger.info("Shutting down LoreGuard API service...")
        
        # Stop background tasks
        if hasattr(app.state, 'job_health_checker'):
            app.state.job_health_checker.stop_monitoring()
            logger.info("Job health checker stopped")
        
        if hasattr(app.state, 'scheduler'):
            app.state.scheduler.stop_scheduler()
            logger.info("Source scheduler stopped")

    # Create FastAPI application
    app = FastAPI(
        title="LoreGuard API",
        description="Facts & Perspectives Harvesting System API",
        version="0.1.0",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan,
        redirect_slashes=False  # Disable automatic trailing slash redirects to prevent CORS issues
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,  # Use configured origins (includes detected IP)
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add trusted host middleware for security
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Allow all hosts for development
    )

    # Include API routes
    app.include_router(api_router, prefix=settings.API_V1_STR)

    @app.get("/")
    async def root():
        """Root endpoint"""
        return {
            "message": "LoreGuard API",
            "version": "0.1.0",
            "status": "operational"
        }

    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "service": "loreguard-api",
            "version": "0.1.0"
        }

    # Exception handler to ensure CORS headers are sent even on errors
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Global exception handler that ensures CORS headers are included"""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        
        # Create error response with CORS headers
        response = JSONResponse(
            status_code=500,
            content={
                "detail": str(exc) if settings.DEBUG else "Internal server error",
                "error": "Internal server error"
            }
        )
        
        # Manually add CORS headers to error response
        origin = request.headers.get("origin")
        if origin and origin in settings.BACKEND_CORS_ORIGINS:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "*"
            response.headers["Access-Control-Allow-Headers"] = "*"
        
        return response

    if __name__ == "__main__":
        import uvicorn
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=settings.PORT,
            reload=settings.DEBUG,
            log_level=settings.LOG_LEVEL.lower()
        )

