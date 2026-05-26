"""
Log Service — business logic for log file management.
Separates concerns from the API route handlers.
"""
import gzip
import logging
import os
from pathlib import Path
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.models import Log

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def count_lines(path: Path) -> int:
    """Count lines in a (optionally gzipped) file efficiently."""
    try:
        opener = gzip.open if path.suffix == ".gz" else open
        with opener(path, "rb") as f:
            return sum(1 for _ in f)
    except Exception as exc:
        logger.warning("Could not count lines in %s: %s", path, exc)
        return 0


def detect_format(filename: str) -> str:
    """Guess log format from filename heuristics."""
    name = filename.lower()
    if "nginx" in name or "access" in name:
        return "nginx_access"
    if "apache" in name:
        return "apache"
    if "syslog" in name or "system" in name:
        return "syslog"
    if "docker" in name:
        return "docker"
    if name.endswith(".json") or name.endswith(".json.log"):
        return "json"
    return "generic"


def get_unique_dest(filename: str) -> Path:
    """
    Return a unique file path inside UPLOAD_DIR.
    If filename already exists, appends a counter to avoid collision.
    """
    dest = UPLOAD_DIR / filename
    if not dest.exists():
        return dest

    stem   = Path(filename).stem
    suffix = "".join(Path(filename).suffixes)
    counter = 1
    while True:
        candidate = UPLOAD_DIR / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


async def get_log_by_id(db: AsyncSession, log_id: str) -> Optional[Log]:
    """Fetch a single log by primary key."""
    return await db.get(Log, log_id)


async def list_logs(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> List[Log]:
    """Return all logs ordered by creation date descending."""
    result = await db.execute(
        select(Log).order_by(Log.created_at.desc()).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def delete_log_and_file(db: AsyncSession, log: Log) -> None:
    """Remove the log record from DB and its file from disk."""
    file_path = Path(log.file_path)
    if file_path.exists():
        try:
            file_path.unlink()
            logger.info("Deleted file: %s", file_path)
        except OSError as exc:
            logger.warning("Could not delete file %s: %s", file_path, exc)
    await db.delete(log)
    logger.info("Deleted log record '%s' (id=%s)", log.filename, log.id)
