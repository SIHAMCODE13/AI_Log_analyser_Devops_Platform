"""
Analysis API — trigger AI analysis and retrieve results.
Business logic delegated to app.services.analysis_service.
"""
import json
import logging
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.models import AnalysisResult, Log
from app.schemas.schemas import AnalysisResultResponse, AnalyzeRequest
from app.services import analysis_service

logger = logging.getLogger(__name__)
router = APIRouter()


def _build_result_response(ar: AnalysisResult, filename: str) -> AnalysisResultResponse:
    """Helper: convert ORM + filename into response schema."""
    raw = json.loads(ar.raw_result) if ar.raw_result else {}
    return AnalysisResultResponse(
        id                  = ar.id,
        log_id              = ar.log_id,
        filename            = filename,
        status              = ar.status,
        mode                = ar.mode,
        sensitivity         = ar.sensitivity,
        total_lines         = ar.total_lines,
        anomaly_count       = ar.anomaly_count,
        anomaly_rate        = ar.anomaly_rate,
        top_classification  = ar.top_classification,
        processing_time_ms  = ar.processing_time_ms,
        ai_model_version    = ar.ai_model_version,
        anomalies           = raw.get("anomalies"),
        created_at          = ar.created_at,
        completed_at        = ar.completed_at,
    )


@router.post(
    "/analyze",
    response_model=List[dict],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger AI analysis for one or more logs",
)
async def analyze_logs(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Submit log IDs for AI analysis.
    Returns immediately with result IDs; processing runs asynchronously.
    """
    submitted = []

    for log_id in request.log_ids:
        log = await db.get(Log, log_id)
        if not log:
            raise HTTPException(status_code=404, detail=f"Log '{log_id}' not found")

        result = AnalysisResult(
            log_id      = log_id,
            mode        = request.mode,
            sensitivity = request.sensitivity,
            status      = "pending",
        )
        db.add(result)
        await db.flush()  # get result.id before committing

        background_tasks.add_task(
            analysis_service.run_analysis_task,
            result.id, log_id, request.mode, request.sensitivity,
        )

        submitted.append({
            "result_id": result.id,
            "log_id":    log_id,
            "status":    "pending",
        })

    logger.info("Queued %d analysis job(s)", len(submitted))
    return submitted


@router.get(
    "/results",
    response_model=List[AnalysisResultResponse],
    summary="List all analysis results",
)
async def list_results(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """Return all analysis results with log filename, newest first."""
    rows = await analysis_service.get_all_results(db, skip=skip, limit=limit)
    return [_build_result_response(ar, filename) for ar, filename in rows]


@router.get(
    "/results/{result_id}",
    response_model=AnalysisResultResponse,
    summary="Get a single analysis result by ID",
)
async def get_result(result_id: str, db: AsyncSession = Depends(get_db)):
    """Return detailed result including anomaly list."""
    row = await analysis_service.get_result_by_id(db, result_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Result '{result_id}' not found")
    ar, filename = row
    return _build_result_response(ar, filename)


@router.delete(
    "/results/{result_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an analysis result",
)
async def delete_result(result_id: str, db: AsyncSession = Depends(get_db)):
    """Delete an analysis result record."""
    result = await db.get(AnalysisResult, result_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Result '{result_id}' not found")
    await db.delete(result)
    logger.info("Deleted analysis result %s", result_id)
