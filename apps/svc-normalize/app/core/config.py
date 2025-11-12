"""
LoreGuard Document Processing Service Configuration

Centralized configuration management using Pydantic settings.
"""

import os
from typing import List, Optional, Union
from pydantic import validator, Field
from pydantic_settings import BaseSettings
from pathlib import Path

# Project root: config.py -> core -> app -> svc-normalize -> apps -> LoreGuard (5 levels up)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent

# Note: LOREGUARD_HOST_IP is loaded from .env file via Pydantic Settings below
# No manual loading needed - Pydantic handles it automatically

class Settings(BaseSettings):
    """Application settings."""
    
    # =============================================================================
    # SERVICE CONFIGURATION
    # =============================================================================
    
    SERVICE_NAME: str = "loreguard-normalize"
    SERVICE_VERSION: str = "0.1.0"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    
    # Server configuration
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8001, env="PORT")
    
    # API configuration
    API_V1_STR: str = "/api/v1"
    
    # =============================================================================
    # SECURITY AND CORS
    # =============================================================================
    
    # CORS origins
    _default_cors_origins = [
        f"http://{os.getenv('LOREGUARD_HOST_IP', 'localhost')}:3000",
        f"http://{os.getenv('LOREGUARD_HOST_IP', 'localhost')}:5173",
        f"http://{os.getenv('LOREGUARD_HOST_IP', 'localhost')}:6060",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:6060"
    ]
    
    BACKEND_CORS_ORIGINS: Union[str, List[str]] = Field(
        default_factory=lambda: ",".join(_default_cors_origins),
        env="BACKEND_CORS_ORIGINS"
    )
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        _defaults = [
            f"http://{os.getenv('LOREGUARD_HOST_IP', 'localhost')}:3000",
            f"http://{os.getenv('LOREGUARD_HOST_IP', 'localhost')}:5173",
            f"http://{os.getenv('LOREGUARD_HOST_IP', 'localhost')}:6060",
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:6060"
        ]
        if v is None:
            return _defaults
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            # Handle comma-separated string
            if v.startswith("["):
                # Try to parse as JSON array
                import json
                try:
                    return json.loads(v)
                except:
                    pass
            # Split comma-separated string
            return [i.strip() for i in v.split(",") if i.strip()]
        return _defaults
    
    # Allowed hosts
    ALLOWED_HOSTS: Union[str, List[str]] = Field(
        default_factory=lambda: "*",  # Allow all hosts in development
        env="ALLOWED_HOSTS"
    )
    
    @validator("ALLOWED_HOSTS", pre=True)
    def assemble_allowed_hosts(cls, v: Union[str, List[str]]) -> List[str]:
        _defaults = [
            os.getenv('LOREGUARD_HOST_IP', 'localhost'),
            "localhost",
            "127.0.0.1",
            "0.0.0.0",
            "*"  # Allow all hosts in development
        ]
        if v is None:
            return _defaults
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            # Handle "*" as allow all
            if v == "*":
                return ["*"]
            # Handle comma-separated string
            if v.startswith("["):
                # Try to parse as JSON array
                import json
                try:
                    return json.loads(v)
                except:
                    pass
            # Split comma-separated string
            return [i.strip() for i in v.split(",") if i.strip()]
        return _defaults
    
    # =============================================================================
    # DATABASE CONFIGURATION
    # =============================================================================
    
    # PostgreSQL database
    DATABASE_URL: str = Field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL",
            f"postgresql://loreguard:loreguard123@{os.getenv('LOREGUARD_HOST_IP', 'localhost')}:5432/loreguard"
        ),
        env="DATABASE_URL"
    )
    
    # Database connection pool
    DB_POOL_SIZE: int = Field(default=10, env="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(default=20, env="DB_MAX_OVERFLOW")
    DB_POOL_TIMEOUT: int = Field(default=30, env="DB_POOL_TIMEOUT")
    
    # =============================================================================
    # REDIS CONFIGURATION
    # =============================================================================
    
    REDIS_URL: str = Field(
        default=f"redis://{os.getenv('LOREGUARD_HOST_IP', 'localhost')}:6379/0",
        env="REDIS_URL"
    )
    REDIS_TIMEOUT: int = Field(default=5, env="REDIS_TIMEOUT")
    
    # =============================================================================
    # OBJECT STORAGE CONFIGURATION
    # =============================================================================
    
    # MinIO/S3 configuration
    S3_ENDPOINT_URL: Optional[str] = Field(
        default=f"http://{os.getenv('LOREGUARD_HOST_IP', 'localhost')}:9000",
        env="S3_ENDPOINT_URL"
    )
    S3_ACCESS_KEY_ID: str = Field(default="loreguard", env="S3_ACCESS_KEY_ID")  # From docker-compose
    S3_SECRET_ACCESS_KEY: str = Field(default="minio_password_here", env="S3_SECRET_ACCESS_KEY")  # From docker-compose
    S3_BUCKET_NAME: str = Field(default="loreguard-artifacts", env="S3_BUCKET_NAME")
    S3_REGION: str = Field(default="us-east-1", env="S3_REGION")
    
    # =============================================================================
    # DOCUMENT PROCESSING CONFIGURATION
    # =============================================================================
    
    # File upload limits
    MAX_FILE_SIZE: int = Field(default=100 * 1024 * 1024, env="MAX_FILE_SIZE")  # 100MB
    MAX_FILES_PER_REQUEST: int = Field(default=10, env="MAX_FILES_PER_REQUEST")
    
    # Supported file types
    SUPPORTED_MIME_TYPES: List[str] = Field(
        default=[
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/msword",
            "application/vnd.ms-powerpoint",
            "application/vnd.ms-excel",
            "text/html",
            "text/plain",
            "text/markdown",
            "text/xml",
            "application/xml",
            "application/json",
            "image/jpeg",
            "image/png",
            "image/tiff",
            "image/bmp"
        ],
        env="SUPPORTED_MIME_TYPES"
    )
    
    # Processing timeouts
    PROCESSING_TIMEOUT: int = Field(default=300, env="PROCESSING_TIMEOUT")  # 5 minutes
    OCR_TIMEOUT: int = Field(default=120, env="OCR_TIMEOUT")  # 2 minutes
    
    # =============================================================================
    # OCR CONFIGURATION
    # =============================================================================
    
    # Tesseract OCR settings
    TESSERACT_CMD: Optional[str] = Field(default=None, env="TESSERACT_CMD")
    TESSERACT_LANGUAGES: str = Field(default="eng+fra+deu+spa+rus+chi_sim", env="TESSERACT_LANGUAGES")
    
    # OCR quality settings
    OCR_DPI: int = Field(default=300, env="OCR_DPI")
    OCR_CONFIDENCE_THRESHOLD: float = Field(default=60.0, env="OCR_CONFIDENCE_THRESHOLD")
    
    # =============================================================================
    # LANGUAGE PROCESSING CONFIGURATION
    # =============================================================================
    
    # Language detection
    LANGUAGE_DETECTION_ENABLED: bool = Field(default=True, env="LANGUAGE_DETECTION_ENABLED")
    DEFAULT_LANGUAGE: str = Field(default="en", env="DEFAULT_LANGUAGE")
    
    # Supported languages for processing
    SUPPORTED_LANGUAGES: List[str] = Field(
        default=["en", "fr", "de", "es", "ru", "zh", "ar", "pt", "it", "ja"],
        env="SUPPORTED_LANGUAGES"
    )
    
    @validator("SUPPORTED_LANGUAGES", pre=True)
    def assemble_supported_languages(cls, v) -> List[str]:
        if v is None:
            return ["en", "fr", "de", "es", "ru", "zh", "ar", "pt", "it", "ja"]
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            # Handle comma-separated string
            if "," in v:
                return [i.strip() for i in v.split(",") if i.strip()]
            # Handle JSON list string
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            # Single value
            return [v.strip()] if v.strip() else []
        raise ValueError(f"Invalid SUPPORTED_LANGUAGES format: {v}")
    
    # =============================================================================
    # CONTENT PROCESSING CONFIGURATION
    # =============================================================================
    
    # Text extraction settings
    MIN_TEXT_LENGTH: int = Field(default=100, env="MIN_TEXT_LENGTH")
    MAX_TEXT_LENGTH: int = Field(default=1000000, env="MAX_TEXT_LENGTH")  # 1MB
    
    # Content quality thresholds
    MIN_CONFIDENCE_SCORE: float = Field(default=0.5, env="MIN_CONFIDENCE_SCORE")
    
    # Metadata extraction
    EXTRACT_METADATA: bool = Field(default=True, env="EXTRACT_METADATA")
    EXTRACT_IMAGES: bool = Field(default=False, env="EXTRACT_IMAGES")
    EXTRACT_TABLES: bool = Field(default=True, env="EXTRACT_TABLES")
    
    # =============================================================================
    # LOGGING CONFIGURATION
    # =============================================================================
    
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="json", env="LOG_FORMAT")  # json or text
    LOG_FILE: Optional[str] = Field(default=None, env="LOG_FILE")
    
    # =============================================================================
    # MONITORING CONFIGURATION
    # =============================================================================
    
    # Prometheus metrics
    METRICS_ENABLED: bool = Field(default=True, env="METRICS_ENABLED")
    METRICS_PORT: int = Field(default=8002, env="METRICS_PORT")
    
    # Health check configuration
    HEALTH_CHECK_TIMEOUT: int = Field(default=10, env="HEALTH_CHECK_TIMEOUT")
    
    # =============================================================================
    # EXTERNAL SERVICES
    # =============================================================================
    
    # Other LoreGuard services
    # In Docker, use service name; otherwise use host IP
    # Check if we're in Docker by checking if service name resolves
    _default_api_url = os.getenv('API_SERVICE_URL')
    if not _default_api_url:
        # Try Docker service name first (for container-to-container communication)
        _default_api_url = "http://loreguard-api:8000"
    
    API_SERVICE_URL: str = Field(
        default=_default_api_url,
        env="API_SERVICE_URL"
    )
    INGESTION_SERVICE_URL: str = Field(
        default=f"http://{os.getenv('LOREGUARD_HOST_IP', 'localhost')}:8003",
        env="INGESTION_SERVICE_URL"
    )
    
    # =============================================================================
    # DEVELOPMENT SETTINGS
    # =============================================================================
    
    # Development mode settings
    DEBUG: bool = Field(default=False, env="DEBUG")
    RELOAD: bool = Field(default=False, env="RELOAD")
    
    # Testing
    TESTING: bool = Field(default=False, env="TESTING")
    TEST_DATABASE_URL: Optional[str] = Field(default=None, env="TEST_DATABASE_URL")
    
    class Config:
        # Single source of truth: .env file in project root
        # Docker Compose and all services read from this file
        env_file = [
            str(PROJECT_ROOT / ".env"),  # Project root .env (single source of truth)
            ".env"                       # Local .env (fallback for service-specific overrides)
        ]
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields from .env files


# Create settings instance
settings = Settings()

