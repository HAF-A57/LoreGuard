"""
Simple test endpoints to validate API functionality
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from db.database import get_db

router = APIRouter()

@router.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return {"message": "pong", "status": "healthy"}

@router.get("/db-test")
async def test_database(db: Session = Depends(get_db)):
    """Test database connectivity"""
    try:
        # Simple query to test database
        result = db.execute(text("SELECT 1 as test")).fetchone()
        
        # Count tables
        tables_result = db.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """)).fetchall()
        
        table_names = [row[0] for row in tables_result]
        
        return {
            "database_connected": True,
            "test_query_result": result[0] if result else None,
            "tables_created": table_names,
            "table_count": len(table_names)
        }
    except Exception as e:
        return {
            "database_connected": False,
            "error": str(e)
        }

@router.get("/sources-simple")
async def list_sources_simple(db: Session = Depends(get_db)):
    """Simple sources list without complex relationships"""
    try:
        result = db.execute(text("SELECT id, name, type, status FROM sources")).fetchall()
        
        sources = []
        for row in result:
            sources.append({
                "id": row[0],
                "name": row[1], 
                "type": row[2],
                "status": row[3]
            })
            
        return {
            "sources": sources,
            "count": len(sources)
        }
    except Exception as e:
        return {
            "error": str(e),
            "sources": [],
            "count": 0
        }

@router.get("/artifacts-simple")
async def list_artifacts_simple(db: Session = Depends(get_db)):
    """Simple artifacts list without complex relationships"""
    try:
        result = db.execute(text("""
            SELECT a.id, a.uri, a.content_hash, a.created_at,
                   dm.title, dm.organization
            FROM artifacts a
            LEFT JOIN document_metadata dm ON a.id = dm.artifact_id
            LIMIT 10
        """)).fetchall()
        
        artifacts = []
        for row in result:
            artifacts.append({
                "id": row[0],
                "uri": row[1],
                "content_hash": row[2],
                "created_at": str(row[3]) if row[3] else None,
                "title": row[4],
                "organization": row[5]
            })
            
        return {
            "artifacts": artifacts,
            "count": len(artifacts)
        }
    except Exception as e:
        return {
            "error": str(e),
            "artifacts": [],
            "count": 0
        }

