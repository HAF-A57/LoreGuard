"""
LoreGuard AI Assistant Service Configuration

Centralized configuration management using Pydantic settings.
"""

import os
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from pathlib import Path

# Project root: config.py -> core -> app -> svc-assistant -> apps -> LoreGuard (5 levels up)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent

# Note: LOREGUARD_HOST_IP is loaded from .env file via Pydantic Settings below
# No manual loading needed - Pydantic handles it automatically

class Settings(BaseSettings):
    """Application settings"""
    
    # =============================================================================
    # SERVICE CONFIGURATION
    # =============================================================================
    
    SERVICE_NAME: str = "loreguard-assistant"
    SERVICE_VERSION: str = "0.1.0"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    
    # Server configuration
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8002, env="PORT")
    
    # API configuration
    API_V1_STR: str = "/api/v1"
    
    # =============================================================================
    # SECURITY AND CORS
    # =============================================================================
    
    # CORS origins - computed property to use LOREGUARD_HOST_IP
    @property
    def BACKEND_CORS_ORIGINS(self) -> List[str]:
        """Get CORS origins using detected host IP"""
        explicit = os.getenv("BACKEND_CORS_ORIGINS")
        if explicit:
            return [origin.strip() for origin in explicit.split(",")]
        
        host_ip = self.LOREGUARD_HOST_IP
        return [
            f"http://{host_ip}:3000",
            f"http://{host_ip}:5173",
            f"http://{host_ip}:6060",
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:6060"
        ]
    
    # =============================================================================
    # DATABASE CONFIGURATION
    # =============================================================================
    
    # PostgreSQL database - Pydantic will construct this using env vars
    POSTGRES_PASSWORD: str = Field(default="VHR829WfKVoH9LwtNXtc67lRe", env="POSTGRES_PASSWORD")
    LOREGUARD_HOST_IP: str = Field(default="localhost", env="LOREGUARD_HOST_IP")
    
    @property
    def DATABASE_URL(self) -> str:
        """Construct database URL from environment variables"""
        explicit_url = os.getenv("DATABASE_URL")
        if explicit_url:
            return explicit_url
        return f"postgresql://loreguard:{self.POSTGRES_PASSWORD}@{self.LOREGUARD_HOST_IP}:5432/loreguard"
    
    # Database connection pool
    # Reduced pool sizes for assistant service (3-5 connections)
    DB_POOL_SIZE: int = Field(default=3, env="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(default=5, env="DB_MAX_OVERFLOW")
    
    # =============================================================================
    # REDIS CONFIGURATION
    # =============================================================================
    
    @property
    def REDIS_URL(self) -> str:
        """Construct Redis URL from environment variables"""
        explicit_url = os.getenv("REDIS_URL")
        if explicit_url:
            # If explicit URL, use it with DB 1 for assistant
            if '/' in explicit_url:
                base = explicit_url.rsplit('/', 1)[0]
                return f"{base}/1"
            return f"{explicit_url}/1"
        return f"redis://{self.LOREGUARD_HOST_IP}:6379/1"
    
    # =============================================================================
    # AI/LLM CONFIGURATION
    # =============================================================================
    
    # Context window management
    MAX_CONTEXT_TOKENS: int = Field(default=30000, env="MAX_CONTEXT_TOKENS")
    MAX_COMPLETION_TOKENS: int = Field(default=2000, env="MAX_COMPLETION_TOKENS")
    CONTEXT_COMPRESSION_THRESHOLD: float = Field(default=0.8, env="CONTEXT_COMPRESSION_THRESHOLD")  # Start compression at 80% of max
    
    # Default LLM configuration (fallback if user hasn't configured)
    DEFAULT_LLM_MODEL: str = Field(default="gpt-4", env="DEFAULT_LLM_MODEL")
    DEFAULT_LLM_TEMPERATURE: float = Field(default=0.7, env="DEFAULT_LLM_TEMPERATURE")
    
    # RAG configuration
    ENABLE_RAG: bool = Field(default=True, env="ENABLE_RAG")
    RAG_TOP_K: int = Field(default=5, env="RAG_TOP_K")  # Number of relevant items to retrieve
    EMBEDDING_MODEL: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", env="EMBEDDING_MODEL")
    
    # =============================================================================
    # EXTERNAL SERVICES
    # =============================================================================
    
    # Other LoreGuard services - computed properties
    @property
    def API_SERVICE_URL(self) -> str:
        """Get API service URL"""
        return os.getenv("API_SERVICE_URL", f"http://{self.LOREGUARD_HOST_IP}:8000")
    
    @property
    def NORMALIZE_SERVICE_URL(self) -> str:
        """Get normalize service URL"""
        return os.getenv("NORMALIZE_SERVICE_URL", f"http://{self.LOREGUARD_HOST_IP}:8001")
    
    # =============================================================================
    # CHAT CONFIGURATION
    # =============================================================================
    
    # Session management
    SESSION_TIMEOUT_HOURS: int = Field(default=24, env="SESSION_TIMEOUT_HOURS")
    MAX_SESSIONS_PER_USER: int = Field(default=50, env="MAX_SESSIONS_PER_USER")
    
    # Message limits
    MAX_MESSAGE_LENGTH: int = Field(default=10000, env="MAX_MESSAGE_LENGTH")
    MAX_MESSAGES_PER_SESSION: int = Field(default=500, env="MAX_MESSAGES_PER_SESSION")
    
    # Context window management
    AUTO_SUMMARIZE_ENABLED: bool = Field(default=True, env="AUTO_SUMMARIZE_ENABLED")
    SUMMARIZATION_INTERVAL: int = Field(default=20, env="SUMMARIZATION_INTERVAL")  # Summarize every N messages
    
    # =============================================================================
    # LOGGING CONFIGURATION
    # =============================================================================
    
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="json", env="LOG_FORMAT")  # json or text
    
    # =============================================================================
    # DEVELOPMENT SETTINGS
    # =============================================================================
    
    DEBUG: bool = Field(default=False, env="DEBUG")
    RELOAD: bool = Field(default=False, env="RELOAD")
    
    class Config:
        # Single source of truth: .env file in project root
        # Docker Compose and all services read from this file
        env_file = [
            str(PROJECT_ROOT / ".env"),  # Project root .env (single source of truth)
            ".env"                       # Local .env (fallback for service-specific overrides)
        ]
        case_sensitive = True
        extra = "ignore"


# Create settings instance
settings = Settings()

