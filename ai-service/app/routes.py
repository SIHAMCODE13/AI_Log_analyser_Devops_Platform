"""
AI Service API routes.
"""
import logging
import time
from typing import List, Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────
class PredictRequest(BaseModel):
    log_id:    str
    filename:  str
    log_format: str = "generic"
    mode:       Literal["auto", "anomaly", "classification", "both"] = "auto"
    sensitivity: int = Field(default=7, ge=1, le=10)
    lines:      List[str]


class HealthResponse(BaseModel):
    status:        str
    model_version: str
    model_loaded:  bool


# ── Routes ────────────────────────────────────────────────────────────────────
@router.get("/health", response_model=HealthResponse)
async def health():
    from app.main import predictor
    return HealthResponse(
        status        = "healthy" if predictor and predictor._trained else "loading",
        model_version = predictor.version if predictor else "N/A",
        model_loaded  = predictor._trained if predictor else False,
    )


@router.post("/predict")
async def predict(request: PredictRequest):
    """
    Main prediction endpoint.
    Accepts log lines, returns anomalies and classifications.
    """
    from app.main import predictor, PREDICTION_COUNT, PREDICTION_LATENCY

    if not predictor or not predictor._trained:
        raise HTTPException(status_code=503, detail="Model not ready")

    PREDICTION_COUNT.inc()

    start = time.perf_counter()
    try:
        result = predictor.predict(
            lines       = request.lines,
            mode        = request.mode,
            sensitivity = request.sensitivity,
        )
    except Exception as exc:
        logger.exception("Prediction failed for log_id=%s", request.log_id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    elapsed = time.perf_counter() - start
    PREDICTION_LATENCY.observe(elapsed)

    result["log_id"]           = request.log_id
    result["processing_time_ms"] = int(elapsed * 1000)

    logger.info(
        "Predicted log_id=%s lines=%d anomalies=%d in %.0fms",
        request.log_id, len(request.lines), result["anomaly_count"], elapsed * 1000,
    )
    return result


@router.get("/model/info")
async def model_info():
    """Return detailed model metadata."""
    from app.main import predictor
    if not predictor:
        raise HTTPException(status_code=503, detail="Model not ready")
    return {
        "version":    predictor.version,
        "algorithms": ["IsolationForest", "RandomForestClassifier"],
        "features":   predictor.extractor.feature_names,
        "classes":    list(predictor.classifier.classes_) if predictor._trained else [],
    }
