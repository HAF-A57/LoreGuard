"""
Health check endpoints for document processing service.
"""

from fastapi import APIRouter, Depends
from app.services.health import HealthService
from app.schemas.document import ServiceHealth

router = APIRouter()

@router.get("/", response_model=dict)
async def health_check():
    """Basic health check endpoint."""
    health_service = HealthService()
    return await health_service.get_health_status()

