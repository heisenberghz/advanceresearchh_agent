"""Health and readiness router."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from app.config import Settings, get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def get_health(settings: Settings = Depends(get_settings)):
    """Health check endpoint.

    Returns operational status, version, and external service configuration readiness
    without exposing any sensitive API keys.
    """
    missing_keys = settings.check_missing_required_keys()

    return {
        "status": "healthy",
        "service": "ResearchOps Backend",
        "version": "0.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": settings.environment,
        "configuration": {
            "is_research_ready": len(missing_keys) == 0,
            "missing_keys": missing_keys,
            "research_model": settings.research_model,
            "writer_model": settings.writer_model,
            "max_research_retries": settings.max_research_retries,
            "max_searches_per_job": settings.max_searches_per_job,
        },
    }
