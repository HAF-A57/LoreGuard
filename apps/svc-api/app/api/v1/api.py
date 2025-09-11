"""
Main API router combining all endpoint modules
"""

from fastapi import APIRouter

from api.v1.endpoints import artifacts, sources, rubrics, evaluations, jobs, library, test

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(test.router, prefix="/test", tags=["test"])
api_router.include_router(artifacts.router, prefix="/artifacts", tags=["artifacts"])
api_router.include_router(sources.router, prefix="/sources", tags=["sources"])
api_router.include_router(rubrics.router, prefix="/rubrics", tags=["rubrics"])
api_router.include_router(evaluations.router, prefix="/evaluations", tags=["evaluations"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(library.router, prefix="/library", tags=["library"])

