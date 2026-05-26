"""
Application configuration — loaded from environment variables.
Uses pydantic-settings for type-safe config management.
"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── App ─────────────────────────────────────────────────────────────
    APP_NAME:    str = "AI DevOps Log Analyzer"
    APP_VERSION: str = "1.0.0"
    DEBUG:       bool = False

    # ── Database ─────────────────────────────────────────────────────────
    DATABASE_URL: str = "mysql+aiomysql://loguser:logpass@mysql:3306/loganalyzer"

    # ── AI Service ───────────────────────────────────────────────────────
    AI_SERVICE_URL: str = "http://ai-service:8001"
    AI_SERVICE_TIMEOUT: int = 120  # seconds

    # ── File Upload ──────────────────────────────────────────────────────
    UPLOAD_DIR:       str  = "/app/uploads"
    MAX_FILE_SIZE_MB: int  = 100
    ALLOWED_EXTENSIONS: List[str] = [".log", ".txt", ".gz"]

    # ── Security ─────────────────────────────────────────────────────────
    SECRET_KEY: str = "change-me-in-production-use-strong-random-key"
    API_KEY:    str = "dev-api-key-change-in-production"

    # ── CORS ─────────────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:80",
        "http://localhost:3000",
        "http://frontend",
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
