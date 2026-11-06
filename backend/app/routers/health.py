"""Process health. This route is unauthenticated and returns no secrets."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.deps import get_db
from app.schemas import HealthCheck
from app.services.media_inspector import tool_available
from app.version import PHASE, __version__

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthCheck)
def health(db: Session = Depends(get_db)) -> HealthCheck:
    checks = {
        "database": _database(db),
        "ffmpeg": "ok" if tool_available("ffmpeg") else "missing",
        "ffprobe": "ok" if tool_available("ffprobe") else "missing",
    }
    status = "ok" if all(value == "ok" for value in checks.values()) else "degraded"
    return HealthCheck(
        status=status,
        version=__version__,
        phase=PHASE,
        time=datetime.now(timezone.utc),
        checks=checks,
    )


def _database(db: Session) -> str:
    try:
        db.execute(text("SELECT 1"))
        return "ok"
    except Exception:  # noqa: BLE001 - health must report the failure instead of raising
        return "error"
