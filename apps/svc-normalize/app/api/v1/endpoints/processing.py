"""
Batch processing endpoints.
"""

from fastapi import APIRouter

router = APIRouter()

@router.post("/batch")
async def process_batch():
    """Process a batch of documents."""
    return {"message": "Batch processing endpoint - coming soon"}

