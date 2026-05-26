"""
Logs API — upload, list, get, delete log files.
Business logic delegated to app.services.log_service.
"""
import logging
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.models import Log
from app.schemas.schemas import LogResponse
from app.services import log_service

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024


@router.post(
    "/logs/upload",
    response_model=List[LogResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload one or more log files",
)
async def upload_logs(
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload log files for AI analysis.
    Supports .log, .txt, .gz formats up to MAX_FILE_SIZE_MB.
    """
    saved: List[Log] = []

    for upload in files:
        ext = Path(upload.filename).suffix.lower()
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unsupported file type '{ext}'. Allowed: {settings.ALLOWED_EXTENSIONS}",
            )

        dest = log_service.get_unique_dest(upload.filename)
        size = 0

        try:
            with dest.open("wb") as out:
                while chunk := await upload.read(1024 * 1024):  # 1 MB chunks
                    size += len(chunk)
                    if size > MAX_BYTES:
                        dest.unlink(missing_ok=True)
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail=f"File exceeds {settings.MAX_FILE_SIZE_MB} MB limit",
                        )
                    out.write(chunk)
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("Failed to save upload '%s'", upload.filename)
            raise HTTPException(status_code=500, detail=f"File save error: {exc}") from exc

        total_lines = log_service.count_lines(dest)
        log_format  = log_service.detect_format(upload.filename)

        log = Log(
            filename    = upload.filename,
            file_path   = str(dest),
            file_size   = size,
            total_lines = total_lines,
            log_format  = log_format,
        )
        db.add(log)
        saved.append(log)

    await db.flush()
    await db.commit()
    logger.info("Uploaded %d log file(s)", len(saved))
    return saved


@router.get(
    "/logs",
    response_model=List[LogResponse],
    summary="List all uploaded logs",
)
async def list_logs(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """Return all uploaded logs ordered by upload date (newest first)."""
    return await log_service.list_logs(db, skip=skip, limit=limit)


@router.get(
    "/logs/{log_id}",
    response_model=LogResponse,
    summary="Get a single log by ID",
)
async def get_log(log_id: str, db: AsyncSession = Depends(get_db)):
    """Return metadata for a single log file."""
    log = await log_service.get_log_by_id(db, log_id)
    if not log:
        raise HTTPException(status_code=404, detail=f"Log '{log_id}' not found")
    return log


@router.delete(
    "/logs/{log_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a log file",
)
async def delete_log(log_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a log file and its metadata. Cascades to any analysis results."""
    log = await log_service.get_log_by_id(db, log_id)
    if not log:
        raise HTTPException(status_code=404, detail=f"Log '{log_id}' not found")
    await log_service.delete_log_and_file(db, log)
