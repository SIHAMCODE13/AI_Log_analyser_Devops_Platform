"""
AI Log Analyzer — AI Microservice
Handles log preprocessing, anomaly detection, and error classification.
"""
import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, make_asgi_app

from app.services.predictor import LogPredictor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# ── Prometheus ────────────────────────────────────────────────────────────────
PREDICTION_COUNT   = Counter("ai_predictions_total",   "Total prediction requests")
PREDICTION_LATENCY = Histogram("ai_prediction_duration_seconds", "Prediction duration")

# ── Global predictor (loaded once at startup) ─────────────────────────────────
predictor: LogPredictor | None = None

MODEL_DIR = Path("/app/models")

@asynccontextmanager
async def lifespan(app: FastAPI):
    global predictor
    logger.info("🤖 Loading AI models...")
    predictor = LogPredictor(model_dir=MODEL_DIR)
    predictor.load_or_train()
    logger.info("✅ AI models ready — version %s", predictor.version)
    yield
    logger.info("👋 AI service shutting down")


app = FastAPI(
    title="AI Log Analyzer — AI Service",
    description="Anomaly detection and error classification for application logs",
    version="2.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# ── Import and include routes ─────────────────────────────────────────────────
from app.routes import router  # noqa: E402
app.include_router(router)
