"""
Health check endpoint — used by Kubernetes liveness/readiness probes.
"""
import time
import logging
from datetime import datetime

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.schemas.schemas import HealthResponse

logger = logging.getLogger(__name__)
router = APIRouter()

_START_TIME = time.time()


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Returns overall system health.
    Checks database connectivity and AI service reachability.
    """
    # Check database
    db_status = "unhealthy"
    try:
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as exc:
        logger.warning("DB health check failed: %s", exc)
        try:
            await db.rollback()
        except Exception:
            pass

    # Check AI service
    ai_status = "unhealthy"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.AI_SERVICE_URL}/health")
            if resp.status_code == 200:
                ai_status = "healthy"
    except Exception as exc:
        logger.warning("AI service health check failed: %s", exc)

    overall = "healthy" if db_status == ai_status == "healthy" else "degraded"

    return HealthResponse(
        status          = overall,
        version         = settings.APP_VERSION,
        database        = db_status,
        ai_service      = ai_status,
        uptime_seconds  = time.time() - _START_TIME,
    )
