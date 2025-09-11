"""
Jobs API endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.database import get_db

router = APIRouter()

@router.get("/")
async def list_jobs(db: Session = Depends(get_db)):
    """List jobs"""
    return {"message": "Jobs endpoint - coming soon"}

