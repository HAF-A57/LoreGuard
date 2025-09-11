"""
Evaluations API endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.database import get_db

router = APIRouter()

@router.get("/")
async def list_evaluations(db: Session = Depends(get_db)):
    """List evaluations"""
    return {"message": "Evaluations endpoint - coming soon"}

