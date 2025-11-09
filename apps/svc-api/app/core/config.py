"""
LoreGuard API Configuration
Centralized configuration management using Pydantic Settings
"""

from pydantic import validator, Field
from pydantic_settings import BaseSettings
from typing import List, Optional, Union
import secrets
import os
from pathlib import Path

# Project root: config.py -> core -> app -> svc-api -> apps -> LoreGuard (5 levels up)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent

# Note: LOREGUARD_HOST_IP is loaded from .env file via Pydantic Settings below
# No manual loading needed - Pydantic handles it automatically

class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Server Configuration
    PORT: int = 8000
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # CORS Configuration
    # Default to detected IP with common frontend ports, plus localhost fallback
    # Note: Computed at runtime to ensure LOREGUARD_HOST_IP is read from .env file
    BACKEND_CORS_ORIGINS: Union[str, List[str]] = Field(
        default_factory=lambda: ",".join([
            f"http://{os.getenv('LOREGUARD_HOST_IP', 'localhost')}:3000",
            f"http://{os.getenv('LOREGUARD_HOST_IP', 'localhost')}:5173",
            f"http://{os.getenv('LOREGUARD_HOST_IP', 'localhost')}:6060",
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:6060"
        ])
    )
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        # Default origins computed at runtime
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
    
    # Database Configuration
    DATABASE_URL: str = Field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL",
            f"postgresql://loreguard:{os.getenv('POSTGRES_PASSWORD', 'VHR829WfKVoH9LwtNXtc67lRe')}@{os.getenv('LOREGUARD_HOST_IP', 'localhost')}:5432/loreguard"
        )
    )
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Redis Configuration
    REDIS_URL: str = Field(
        default_factory=lambda: os.getenv(
            "REDIS_URL",
            f"redis://{os.getenv('LOREGUARD_HOST_IP', 'localhost')}:6379"
        )
    )
    REDIS_PASSWORD: Optional[str] = Field(default_factory=lambda: os.getenv("REDIS_PASSWORD"))
    
    # MinIO Configuration
    MINIO_ENDPOINT: str = Field(
        default_factory=lambda: os.getenv(
            "MINIO_ENDPOINT",
            f"{os.getenv('LOREGUARD_HOST_IP', 'localhost')}:9000"
        )
    )
    MINIO_ACCESS_KEY: str = Field(default_factory=lambda: os.getenv("MINIO_ACCESS_KEY", "loreguard"))
    MINIO_SECRET_KEY: str = Field(default_factory=lambda: os.getenv("MINIO_SECRET_KEY", "minio_password_here"))
    MINIO_SECURE: bool = False
    MINIO_BUCKET_NAME: str = "loreguard-artifacts"
    
    # LLM Configuration
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    DEFAULT_LLM_MODEL: str = "gpt-4"
    
    # Processing Configuration
    MAX_CONCURRENT_EVALUATIONS: int = 10
    EVALUATION_TIMEOUT_SECONDS: int = 300
    
    # Security Configuration
    ALGORITHM: str = "HS256"
    
    # Temporal Configuration
    TEMPORAL_HOST: str = Field(
        default_factory=lambda: os.getenv("TEMPORAL_HOST", os.getenv("LOREGUARD_HOST_IP", "localhost"))
    )
    TEMPORAL_PORT: int = 7233
    TEMPORAL_NAMESPACE: str = "default"
    
    class Config:
        # Single source of truth: .env file in project root
        # Docker Compose and all services read from this file
        env_file = [
            str(PROJECT_ROOT / ".env"),  # Project root .env (single source of truth)
            ".env"                       # Local .env (fallback for service-specific overrides)
        ]
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields from .env file

# Create global settings instance
settings = Settings()

