"""
LoreGuard Document Processing Service API Router

Main API router that includes all endpoint routers.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import documents, health, processing


api_router = APIRouter()

# Include endpoint routers
api_router.include_router(
    health.router,
    prefix="/health",
    tags=["health"]
)

api_router.include_router(
    documents.router,
    prefix="/documents",
    tags=["documents"]
)

api_router.include_router(
    processing.router,
    prefix="/processing",
    tags=["processing"]
)

