"""
Rubrics API endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.database import get_db

router = APIRouter()

@router.get("/")
async def list_rubrics(db: Session = Depends(get_db)):
    """List all rubrics"""
    return {"message": "Rubrics endpoint - coming soon"}

@router.get("/active")
async def get_active_rubric(db: Session = Depends(get_db)):
    """Get the currently active rubric"""
    return {"message": "Active rubric endpoint - coming soon"}

