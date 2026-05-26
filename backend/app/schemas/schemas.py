"""
Pydantic schemas for request/response validation.
"""
from __future__ import annotations
from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator


# ── Log schemas ───────────────────────────────────────────────────────────────
class LogBase(BaseModel):
    filename: str
    file_size: int = 0
    total_lines: int = 0
    log_format: Optional[str] = None


class LogCreate(LogBase):
    file_path: str
    user_id: Optional[str] = None


class LogResponse(LogBase):
    id: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Analysis schemas ──────────────────────────────────────────────────────────
class AnalyzeRequest(BaseModel):
    log_ids: List[str] = Field(..., min_length=1, description="List of log IDs to analyze")
    mode: Literal["auto", "anomaly", "classification", "both"] = "auto"
    sensitivity: int = Field(default=7, ge=1, le=10, description="Detection sensitivity (1-10)")


class AnomalyItem(BaseModel):
    line_number: int
    message: str
    severity: Literal["critical", "high", "medium", "low"]
    classification: str
    confidence: float = Field(ge=0.0, le=1.0)
    anomaly_score: float


class AnalysisResultResponse(BaseModel):
    id: str
    log_id: str
    filename: str
    status: str
    mode: str
    sensitivity: int
    total_lines: int
    anomaly_count: int
    anomaly_rate: float
    top_classification: Optional[str]
    processing_time_ms: int
    ai_model_version: Optional[str]
    anomalies: Optional[List[AnomalyItem]] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Stats schemas ─────────────────────────────────────────────────────────────
class DashboardStats(BaseModel):
    total_logs: int
    total_analyses: int
    total_anomalies: int
    avg_anomaly_rate: float
    recent_analyses: List[dict] = []


# ── Health schemas ────────────────────────────────────────────────────────────
class HealthResponse(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"]
    version: str
    database: str
    ai_service: str
    uptime_seconds: float
