"""
Shared database engine module for normalize service

Provides a singleton database engine that is reused across all tasks,
preventing connection pool exhaustion.
"""

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)

# Module-level singleton engine
_engine = None
_Session = None


def get_engine():
    """
    Get or create the shared database engine (singleton pattern).
    
    This engine is created once at module import and reused across all tasks.
    This prevents connection pool exhaustion from creating multiple engines.
    
    Returns:
        SQLAlchemy engine instance
    """
    global _engine
    
    if _engine is None:
        # Use reduced pool size for worker processes (3-5 connections per worker)
        # With 4 concurrent workers, this gives us 12-20 connections max
        pool_size = 3  # Reduced from 10 for worker processes
        max_overflow = 5  # Reduced from 20 for worker processes
        
        _engine = create_engine(
            settings.DATABASE_URL,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=3600,  # Recycle connections after 1 hour
            echo=False
        )
        logger.info(
            f"Created shared database engine with pool_size={pool_size}, "
            f"max_overflow={max_overflow}"
        )
    
    return _engine


def get_session():
    """
    Get a database session using the shared engine.
    
    Returns:
        SQLAlchemy sessionmaker instance
    """
    global _Session
    
    if _Session is None:
        engine = get_engine()
        _Session = sessionmaker(bind=engine)
    
    return _Session()


def dispose_engine():
    """
    Dispose of the shared engine (for cleanup/testing).
    
    Note: This should only be called during shutdown or testing.
    In normal operation, the engine persists for the lifetime of the worker process.
    """
    global _engine, _Session
    
    if _engine is not None:
        _engine.dispose()
        _engine = None
        _Session = None
        logger.info("Disposed shared database engine")

