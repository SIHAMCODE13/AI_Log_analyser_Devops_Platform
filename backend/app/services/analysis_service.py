"""
Analysis Service — business logic for AI analysis orchestration.
Decouples the analysis workflow from the route handlers.
"""
import json
import logging
import time
from datetime import datetime
from typing import List, Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.models import AnalysisResult, Log

logger = logging.getLogger(__name__)

# Maximum lines sent to AI service per request (memory guard)
MAX_LINES = 50_000


async def call_ai_service(log: Log, mode: str, sensitivity: int) -> dict:
    """
    Call the AI microservice /predict endpoint with log content.
    Returns the raw prediction payload on success.
    Raises RuntimeError on file read failure, httpx errors on network failure.
    """
    try:
        with open(log.file_path, "r", errors="replace") as f:
            # Read up to MAX_LINES; readlines() without arg loads all — use islice
            lines = []
            for i, line in enumerate(f):
                if i >= MAX_LINES:
                    break
                lines.append(line.rstrip("\n"))
    except OSError as exc:
        raise RuntimeError(f"Cannot read log file '{log.file_path}': {exc}") from exc

    payload = {
        "log_id":     str(log.id),
        "filename":   log.filename,
        "log_format": log.log_format or "generic",
        "mode":       mode,
        "sensitivity": sensitivity,
        "lines":      lines,
    }

    async with httpx.AsyncClient(timeout=settings.AI_SERVICE_TIMEOUT) as client:
        resp = await client.post(f"{settings.AI_SERVICE_URL}/predict", json=payload)
        resp.raise_for_status()
        return resp.json()


async def run_analysis_task(
    result_id: str,
    log_id: str,
    mode: str,
    sensitivity: int,
) -> None:
    """
    Background task: call AI service, persist results to DB.
    Designed to be run via FastAPI BackgroundTasks.
    """
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        result: Optional[AnalysisResult] = await db.get(AnalysisResult, result_id)
        log:    Optional[Log]            = await db.get(Log, log_id)

        if not result or not log:
            logger.error(
                "run_analysis_task: result_id=%s or log_id=%s not found in DB",
                result_id, log_id,
            )
            return

        result.status = "running"
        await db.commit()

        start = time.perf_counter()
        try:
            ai_response = await call_ai_service(log, mode, sensitivity)
            elapsed_ms  = int((time.perf_counter() - start) * 1000)

            anomalies       = ai_response.get("anomalies", [])
            classifications = [a.get("classification", "") for a in anomalies]
            top_class = (
                max(set(classifications), key=classifications.count)
                if classifications
                else None
            )

            result.status             = "completed"
            result.total_lines        = ai_response.get("total_lines", log.total_lines)
            result.anomaly_count      = len(anomalies)
            result.anomaly_rate       = ai_response.get("anomaly_rate", 0.0)
            result.top_classification = top_class
            result.processing_time_ms = elapsed_ms
            result.ai_model_version   = ai_response.get("model_version", "unknown")
            result.raw_result         = json.dumps(ai_response)
            result.completed_at       = datetime.utcnow()

            logger.info(
                "Analysis %s completed: %d anomalies in %dms",
                result_id, len(anomalies), elapsed_ms,
            )

        except Exception as exc:
            logger.exception("Analysis %s failed: %s", result_id, exc)
            result.status        = "failed"
            result.error_message = str(exc)
            result.completed_at  = datetime.utcnow()

        await db.commit()


async def get_all_results(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
) -> List[tuple]:
    """
    Return (AnalysisResult, filename) tuples ordered by creation date descending.
    """
    stmt = (
        select(AnalysisResult, Log.filename)
        .join(Log, AnalysisResult.log_id == Log.id)
        .order_by(AnalysisResult.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    rows = (await db.execute(stmt)).all()
    return rows


async def get_result_by_id(
    db: AsyncSession, result_id: str
) -> Optional[tuple]:
    """
    Return a single (AnalysisResult, filename) tuple or None.
    """
    stmt = (
        select(AnalysisResult, Log.filename)
        .join(Log, AnalysisResult.log_id == Log.id)
        .where(AnalysisResult.id == result_id)
    )
    row = (await db.execute(stmt)).first()
    return row
