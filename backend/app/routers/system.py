"""Host identity, configuration, capabilities, and the audit trail."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.capabilities import capability_payload
from app.clock import as_utc
from app.config import get_settings
from app.deps import get_db, require_roles, require_user
from app.models import AuditLog, User
from app.schemas import AuditOut, ConfigReport, HostReport
from app.services.system_info import host_report
from app.version import PHASE, __version__

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/host", response_model=HostReport)
def host(_user: User = Depends(require_user)) -> HostReport:
    return host_report()


@router.get("/config", response_model=ConfigReport)
def config(user: User = Depends(require_roles("admin"))) -> ConfigReport:
    settings = get_settings()
    warnings: list[str] = []
    if not settings.localhost_only:
        warnings.append("The API bind address is not loopback. Put it behind an authenticated proxy before exposing it.")
    if not settings.secret_key:
        warnings.append("QUBIT_SECRET_KEY is empty. Set one before treating sessions as stable across restarts.")
    database = "sqlite"
    return ConfigReport(
        app_name=settings.app_name,
        version=__version__,
        phase=PHASE,
        host=settings.host,
        port=settings.port,
        localhost_only=settings.localhost_only,
        database=database,
        media_dir=str(settings.resolved_media_dir()),
        max_upload_bytes=settings.max_upload_bytes,
        token_ttl_hours=settings.token_ttl_hours,
        cors_origins=settings.cors_origin_list,
        warnings=warnings,
    )


@router.get("/capabilities")
def capabilities(_user: User = Depends(require_user)) -> dict[str, object]:
    return capability_payload()


@router.get("/audit", response_model=list[AuditOut])
def audit(db: Session = Depends(get_db), _user: User = Depends(require_roles("admin"))) -> list[AuditOut]:
    rows = db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(100)).all()
    return [
        AuditOut(
            id=row.id,
            created_at=as_utc(row.created_at),
            actor=row.actor,
            action=row.action,
            success=row.success,
            detail=row.detail,
        )
        for row in rows
    ]
