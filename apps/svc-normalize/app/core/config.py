"""
LoreGuard Document Processing Service Configuration

Centralized configuration management using Pydantic settings.
"""

import os
from typing import List, Optional, Union
from pydantic import BaseSettings, validator, Field


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
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"],
        env="BACKEND_CORS_ORIGINS"
    )
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Allowed hosts
    ALLOWED_HOSTS: List[str] = Field(
        default=["localhost", "127.0.0.1", "0.0.0.0"],
        env="ALLOWED_HOSTS"
    )
    
    @validator("ALLOWED_HOSTS", pre=True)
    def assemble_allowed_hosts(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # =============================================================================
    # DATABASE CONFIGURATION
    # =============================================================================
    
    # PostgreSQL database
    DATABASE_URL: str = Field(
        default="postgresql://loreguard:loreguard123@localhost:5432/loreguard",
        env="DATABASE_URL"
    )
    
    # Database connection pool
    DB_POOL_SIZE: int = Field(default=10, env="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(default=20, env="DB_MAX_OVERFLOW")
    DB_POOL_TIMEOUT: int = Field(default=30, env="DB_POOL_TIMEOUT")
    
    # =============================================================================
    # REDIS CONFIGURATION
    # =============================================================================
    
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    REDIS_TIMEOUT: int = Field(default=5, env="REDIS_TIMEOUT")
    
    # =============================================================================
    # OBJECT STORAGE CONFIGURATION
    # =============================================================================
    
    # MinIO/S3 configuration
    S3_ENDPOINT_URL: Optional[str] = Field(default="http://localhost:9000", env="S3_ENDPOINT_URL")
    S3_ACCESS_KEY_ID: str = Field(default="minioadmin", env="S3_ACCESS_KEY_ID")
    S3_SECRET_ACCESS_KEY: str = Field(default="minioadmin", env="S3_SECRET_ACCESS_KEY")
    S3_BUCKET_NAME: str = Field(default="loreguard-documents", env="S3_BUCKET_NAME")
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
    API_SERVICE_URL: str = Field(default="http://localhost:8000", env="API_SERVICE_URL")
    INGESTION_SERVICE_URL: str = Field(default="http://localhost:8003", env="INGESTION_SERVICE_URL")
    
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
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()

