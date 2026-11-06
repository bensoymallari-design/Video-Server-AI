"""Read-only display detection."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.deps import require_user
from app.models import User
from app.schemas import DisplayReport
from app.services.displays import detect_displays

router = APIRouter(prefix="/displays", tags=["displays"])


@router.get("", response_model=DisplayReport)
def list_displays(_user: User = Depends(require_user)) -> DisplayReport:
    return detect_displays()
