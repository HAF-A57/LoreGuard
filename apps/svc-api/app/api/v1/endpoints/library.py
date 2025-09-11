"""
Library API endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.database import get_db

router = APIRouter()

@router.get("/")
async def list_library_items(db: Session = Depends(get_db)):
    """List library items"""
    return {"message": "Library endpoint - coming soon"}

