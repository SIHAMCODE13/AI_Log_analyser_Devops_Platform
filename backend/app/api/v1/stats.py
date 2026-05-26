"""
Stats API — dashboard summary aggregations.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.models import AnalysisResult, Log
from app.schemas.schemas import DashboardStats

router = APIRouter()


@router.get("/stats/dashboard", response_model=DashboardStats)
async def dashboard_stats(db: AsyncSession = Depends(get_db)):
    """Aggregate stats for the dashboard overview."""

    total_logs = (await db.execute(select(func.count(Log.id)))).scalar() or 0

    total_analyses = (
        await db.execute(
            select(func.count(AnalysisResult.id)).where(AnalysisResult.status == "completed")
        )
    ).scalar() or 0

    total_anomalies = (
        await db.execute(select(func.sum(AnalysisResult.anomaly_count)))
    ).scalar() or 0

    avg_rate = (
        await db.execute(select(func.avg(AnalysisResult.anomaly_rate)))
    ).scalar() or 0.0

    # Fetch 10 most recent completed analyses
    recent_stmt = (
        select(AnalysisResult, Log.filename)
        .join(Log, AnalysisResult.log_id == Log.id)
        .where(AnalysisResult.status == "completed")
        .order_by(AnalysisResult.created_at.desc())
        .limit(10)
    )
    recent_rows = (await db.execute(recent_stmt)).all()
    recent = [
        {
            "id":            ar.id,
            "filename":      filename,
            "created_at":    ar.created_at.isoformat(),
            "total_lines":   ar.total_lines,
            "anomaly_count": ar.anomaly_count,
            "status":        ar.status,
        }
        for ar, filename in recent_rows
    ]

    return DashboardStats(
        total_logs       = total_logs,
        total_analyses   = total_analyses,
        total_anomalies  = int(total_anomalies),
        avg_anomaly_rate = round(float(avg_rate), 4),
        recent_analyses  = recent,
    )
