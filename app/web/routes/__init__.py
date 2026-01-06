"""HTTP API routes module.

This module provides:
- Health check endpoints
- Resume data management endpoints
- Chat history management endpoints
"""

from fastapi import APIRouter

from app.web.routes.health import router as health_router
from app.web.routes.resume import router as resume_router
from app.web.routes.history import router as history_router

# Create main API router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(health_router)
api_router.include_router(resume_router)
api_router.include_router(history_router)

__all__ = [
    "api_router",
    "health_router",
    "resume_router",
    "history_router",
]
