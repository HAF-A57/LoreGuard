"""
LoreGuard Document Processing Service

FastAPI service for normalizing and extracting content from various document formats.
Supports PDF, DOCX, HTML, images, and academic papers with metadata extraction.
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.v1.api import api_router
from app.services.health import HealthService


# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    
    # Startup
    logger.info("Starting LoreGuard Document Processing Service")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Service version: {settings.SERVICE_VERSION}")
    
    # Initialize services
    try:
        # Initialize health service
        health_service = HealthService()
        app.state.health_service = health_service
        
        # Initialize document processors
        from app.services.document_processor import DocumentProcessor
        document_processor = DocumentProcessor()
        await document_processor.initialize()
        app.state.document_processor = document_processor
        
        logger.info("Service initialization complete")
        
    except Exception as e:
        logger.error(f"Failed to initialize service: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down LoreGuard Document Processing Service")
    
    # Cleanup resources
    if hasattr(app.state, 'document_processor'):
        await app.state.document_processor.cleanup()


# Create FastAPI application
app = FastAPI(
    title="LoreGuard Document Processing Service",
    description="Document normalization and content extraction service for LoreGuard facts and perspectives harvesting system",
    version=settings.SERVICE_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan
)

# Add middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add trusted host middleware
if settings.ALLOWED_HOSTS:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request, call_next):
    """Add processing time to response headers."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        health_service = app.state.health_service
        health_status = await health_service.get_health_status()
        
        if health_status["status"] == "healthy":
            return health_status
        else:
            return JSONResponse(
                status_code=503,
                content=health_status
            )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "loreguard-normalize",
                "version": settings.SERVICE_VERSION,
                "error": str(e)
            }
        )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "LoreGuard Document Processing Service",
        "version": settings.SERVICE_VERSION,
        "status": "running",
        "docs": f"{settings.API_V1_STR}/docs",
        "health": "/health"
    }


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "message": "An unexpected error occurred"
        }
    )


# Development server
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development",
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    )

