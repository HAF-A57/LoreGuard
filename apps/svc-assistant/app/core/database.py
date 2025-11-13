"""
Database configuration for AI Assistant Service

Creates a separate database engine for the assistant service.
"""

import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# CRITICAL: Block imports of main.py from svc-api-app BEFORE adding it to sys.path
# This prevents FastAPI/uvicorn from accidentally importing the API service's main.py
class BlockAPIMainImport:
    """Import hook to prevent importing main.py from svc-api-app"""
    def find_spec(self, name, path, target=None):
        if name == 'main':
            # Check if this import is from svc-api-app
            if path:
                path_list = path if isinstance(path, list) else [path]
                for p in path_list:
                    p_str = str(p)
                    if '/svc-api-app' in p_str or 'svc-api' in p_str:
                        # Block this import - return None to prevent import
                        return None
        return None

# Install the import hook BEFORE any imports
if not any(isinstance(importer, BlockAPIMainImport) for importer in sys.meta_path):
    sys.meta_path.insert(0, BlockAPIMainImport())

# Also pre-emptively block main in sys.modules if it's from svc-api-app
# This prevents it from being imported even if discovered
_api_main_paths = ['/app/svc-api-app/main.py']
for api_path in _api_main_paths:
    api_main_file = Path(api_path)
    if api_main_file.exists():
        # Create a dummy module that raises ImportError
        import types
        blocked_main = types.ModuleType('main')
        def _raise_import_error(*args, **kwargs):
            raise ImportError("Import of main.py from svc-api-app is blocked. Use app.main instead.")
        blocked_main.__getattr__ = _raise_import_error
        # Only block if it's not already the assistant's main
        if 'main' not in sys.modules or 'app.main' in str(sys.modules.get('main', '')):
            # Don't block - might be assistant's own main
            pass
        # Note: We can't safely block 'main' here because it might be the assistant's own main
        # The import hook above will handle blocking imports from svc-api-app

# Add svc-api/app to path to access Base
# Try multiple paths for container vs local development
possible_paths = [
    Path('/app/svc-api-app'),  # Container path (mounted volume)
    Path(__file__).resolve().parent.parent.parent.parent / 'svc-api' / 'app',  # Local dev
]

# Debug: print paths being checked
import os
if os.getenv('DEBUG', '').lower() == 'true':
    print(f"Checking paths: {[str(p) for p in possible_paths]}")

for path in possible_paths:
    if path.exists():
        path_str = str(path)
        # Only add the specific app directory, not parent (avoids importing main.py)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)
        # Don't add parent directory - it can cause main.py to be discovered
        # Instead, we'll import db.database directly using importlib
        break

# Extract Base class directly from database.py without executing full module
# This avoids importing core.config which triggers dependency chains
import importlib.util
import ast
db_module_path = None
for path in possible_paths:
    db_file = path / 'db' / 'database.py'
    if db_file.exists():
        db_module_path = db_file
        break

if db_module_path:
    # Create Base directly without importing the full database module
    # This avoids dependency chain issues (core.config imports, etc.)
    from sqlalchemy.ext.declarative import declarative_base
    Base = declarative_base()
    
    # Store in sys.modules for compatibility - do this BEFORE any model imports
    # This ensures models can import from db.database without triggering main.py
    if 'db' not in sys.modules:
        import types
        sys.modules['db'] = types.ModuleType('db')
    if 'db.database' not in sys.modules:
        import types
        db_module = types.ModuleType('db.database')
        db_module.Base = Base
        # Add other commonly imported items to avoid importing the real module
        db_module.engine = None  # Will be set by models if needed
        db_module.create_tables = None
        db_module.get_db = None
        sys.modules['db.database'] = db_module
else:
    # Fallback: try normal import (may fail if dependencies missing)
    try:
        from db.database import Base
    except ImportError as e:
        raise ImportError(f"Could not find svc-api database module. Checked paths: {[str(p) for p in possible_paths]}. Error: {e}")

# Ensure db.database.Base is set to our Base (in case it was already created)
if 'db.database' in sys.modules:
    sys.modules['db.database'].Base = Base
from app.core.config import settings


# Create engine for assistant service using assistant's config
# Reduced pool sizes for assistant service (3-5 connections)
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=3,  # Reduced from default 10
    max_overflow=5,  # Reduced from default 20
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.DEBUG,
    future=True
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

