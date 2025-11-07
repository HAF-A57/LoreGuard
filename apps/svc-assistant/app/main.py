"""
LoreGuard AI Assistant Service

FastAPI service for context-aware AI assistant with chat history and tool calling.
"""

# CRITICAL: Import database module FIRST to set up import blocking
# This must happen before any other imports that might trigger svc-api imports
from app.core import database  # This sets up the import blocker

import logging
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.core.config import settings
from app.core.database import engine, Base  # Use assistant's database engine
from app.api.v1.api import api_router
from app.models.chat import ChatSession, ChatMessage

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
    logger.info("Starting LoreGuard AI Assistant Service...")
    
    # Create database tables for chat
    try:
        # Import chat models to register them
        from app.models.chat import ChatSession, ChatMessage
        
        # Create tables
        Base.metadata.create_all(bind=engine, checkfirst=True)
        logger.info("Chat database tables created/verified")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down LoreGuard AI Assistant Service...")


# Create FastAPI application
app = FastAPI(
    title="LoreGuard AI Assistant",
    description="Context-aware AI assistant for LoreGuard facts and perspectives harvesting system",
    version=settings.SERVICE_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Allow all hosts in development
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "LoreGuard AI Assistant",
        "version": settings.SERVICE_VERSION,
        "status": "running",
        "docs": f"{settings.API_V1_STR}/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "loreguard-assistant",
        "version": settings.SERVICE_VERSION
    }


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc) if settings.DEBUG else "Internal server error",
            "error": "Internal server error"
        }
    )


if __name__ == "__main__":
    # Use explicit module path to avoid uvicorn discovering main.py from svc-api-app
    uvicorn.run(
        "app.main:app",  # Explicitly use app.main, not just main
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )

