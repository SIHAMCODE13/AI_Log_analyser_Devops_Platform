"""
SQLAlchemy ORM models — mirrors the MySQL schema.
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    String, Text, Integer, Float, DateTime, Enum, ForeignKey, func, Boolean,
)
from typing import ClassVar, List as TypingList
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


# ── Users ─────────────────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id:         Mapped[str]      = mapped_column(String(36),  primary_key=True, default=_uuid)
    username:   Mapped[str]      = mapped_column(String(64),  unique=True, nullable=False)
    email:      Mapped[str]      = mapped_column(String(255), unique=True, nullable=False)
    is_active:  Mapped[bool]     = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    logs:    Mapped[TypingList["Log"]]            = relationship("Log",            back_populates="user")
    results: Mapped[TypingList["AnalysisResult"]] = relationship("AnalysisResult", back_populates="user")


# ── Logs ──────────────────────────────────────────────────────────────────────
class Log(Base):
    __tablename__ = "logs"

    id:          Mapped[str]      = mapped_column(String(36),  primary_key=True, default=_uuid)
    user_id:     Mapped[str|None] = mapped_column(String(36),  ForeignKey("users.id"), nullable=True)
    filename:    Mapped[str]      = mapped_column(String(255), nullable=False)
    file_path:   Mapped[str]      = mapped_column(Text,        nullable=False)
    file_size:   Mapped[int]      = mapped_column(Integer,     default=0)
    total_lines: Mapped[int]      = mapped_column(Integer,     default=0)
    log_format:  Mapped[str|None] = mapped_column(String(50))
    created_at:  Mapped[datetime] = mapped_column(DateTime,    server_default=func.now())

    user:    Mapped["User"]                       = relationship("User",            back_populates="logs")
    results: Mapped[TypingList["AnalysisResult"]] = relationship("AnalysisResult", back_populates="log")


# ── Analysis Results ──────────────────────────────────────────────────────────
class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id:                  Mapped[str]      = mapped_column(String(36),  primary_key=True, default=_uuid)
    log_id:              Mapped[str]      = mapped_column(String(36),  ForeignKey("logs.id"), nullable=False)
    user_id:             Mapped[str|None] = mapped_column(String(36),  ForeignKey("users.id"), nullable=True)
    status:              Mapped[str]      = mapped_column(
        Enum("pending", "running", "completed", "failed"), default="pending"
    )
    mode:                Mapped[str]      = mapped_column(String(50),  default="auto")
    sensitivity:         Mapped[int]      = mapped_column(Integer,     default=7)
    total_lines:         Mapped[int]      = mapped_column(Integer,     default=0)
    anomaly_count:       Mapped[int]      = mapped_column(Integer,     default=0)
    anomaly_rate:        Mapped[float]    = mapped_column(Float,       default=0.0)
    top_classification:  Mapped[str|None] = mapped_column(String(100))
    processing_time_ms:  Mapped[int]      = mapped_column(Integer,     default=0)
    ai_model_version:    Mapped[str|None] = mapped_column(String(50))
    raw_result:          Mapped[str|None] = mapped_column(Text)   # JSON blob
    error_message:       Mapped[str|None] = mapped_column(Text)
    created_at:          Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    completed_at:        Mapped[datetime|None] = mapped_column(DateTime)

    log:  Mapped["Log"]  = relationship("Log",  back_populates="results")
    user: Mapped["User"] = relationship("User", back_populates="results")
