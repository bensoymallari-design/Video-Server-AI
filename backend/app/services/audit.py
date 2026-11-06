"""Append-only audit records. Details must never include passwords or tokens."""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.models import AuditLog


def record(db: Session, actor: str | None, action: str, success: bool, detail: dict | None = None) -> None:
    db.add(
        AuditLog(
            actor=actor or "anonymous",
            action=action,
            success=success,
            detail=json.dumps(detail or {}, sort_keys=True),
        )
    )
    db.commit()
