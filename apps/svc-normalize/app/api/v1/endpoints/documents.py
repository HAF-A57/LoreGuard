"""
Document processing endpoints.
"""

from fastapi import APIRouter

router = APIRouter()

@router.post("/process")
async def process_document():
    """Process a single document."""
    return {"message": "Document processing endpoint - coming soon"}

