"""Upload, inspection, thumbnail, integrity, and optional proxy transcode."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clock import as_utc
from app.deps import get_db, require_roles, require_user
from app.models import MediaAsset, TranscodeJob, User
from app.schemas import IntegrityOut, MediaOut, TranscodeJobOut
from app.services.audit import record
from app.services.media_store import (
    asset_path,
    create_from_upload,
    delete_asset,
    enqueue_transcode,
    verify_asset,
)

router = APIRouter(prefix="/media", tags=["media"])
_READ = require_roles("admin", "operator", "viewer")
_WRITE = require_roles("admin", "operator")


def _to_out(asset: MediaAsset, duplicate: bool = False) -> MediaOut:
    return MediaOut(
        id=asset.id,
        original_filename=asset.original_filename,
        sha256=asset.sha256,
        size_bytes=asset.size_bytes,
        extension=asset.extension,
        kind=asset.kind,
        container=asset.container,
        video_codec=asset.video_codec,
        audio_codec=asset.audio_codec,
        width=asset.width,
        height=asset.height,
        duration_seconds=asset.duration_seconds,
        frame_rate=asset.frame_rate,
        pixel_format=asset.pixel_format,
        rotation_degrees=asset.rotation_degrees,
        thumbnail_ready=asset.thumbnail_ready,
        has_proxy=asset.has_proxy,
        validation_status=asset.validation_status,
        validation_notes=asset.validation_notes,
        created_at=as_utc(asset.created_at),
        duplicate=duplicate,
    )


def _asset_or_404(db: Session, media_id: str) -> MediaAsset:
    asset = db.get(MediaAsset, media_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Media not found")
    return asset


@router.get("", response_model=list[MediaOut])
def list_media(db: Session = Depends(get_db), _user: User = Depends(_READ)) -> list[MediaOut]:
    rows = db.scalars(select(MediaAsset).order_by(MediaAsset.created_at.desc()).limit(200)).all()
    return [_to_out(row) for row in rows]


@router.post("", response_model=MediaOut)
async def upload_media(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(_WRITE),
) -> MediaOut:
    asset, duplicate = await create_from_upload(db, file)
    record(
        db,
        user.username,
        "media.upload",
        True,
        {"id": asset.id, "filename": asset.original_filename, "duplicate": duplicate, "sha256": asset.sha256},
    )
    return _to_out(asset, duplicate=duplicate)


@router.get("/jobs/{job_id}", response_model=TranscodeJobOut)
def get_job(job_id: str, db: Session = Depends(get_db), _user: User = Depends(_READ)) -> TranscodeJobOut:
    job = db.get(TranscodeJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Transcode job not found")
    return _job_out(job)


@router.get("/{media_id}", response_model=MediaOut)
def get_media(media_id: str, db: Session = Depends(get_db), _user: User = Depends(_READ)) -> MediaOut:
    return _to_out(_asset_or_404(db, media_id))


@router.get("/{media_id}/thumbnail")
def thumbnail(media_id: str, db: Session = Depends(get_db), _user: User = Depends(_READ)) -> FileResponse:
    asset = _asset_or_404(db, media_id)
    if not asset.thumbnail_ready:
        raise HTTPException(status_code=404, detail="Thumbnail is not available")
    path = asset_path(asset, "thumbnail.jpg")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Thumbnail file is missing")
    return FileResponse(path, media_type="image/jpeg")


@router.get("/{media_id}/probe")
def probe(media_id: str, db: Session = Depends(get_db), _user: User = Depends(_WRITE)) -> dict:
    asset = _asset_or_404(db, media_id)
    path = asset_path(asset, "probe.json")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Probe data is not available")
    return json.loads(path.read_text(encoding="utf-8"))


@router.get("/{media_id}/verify", response_model=IntegrityOut)
def verify(media_id: str, db: Session = Depends(get_db), user: User = Depends(_READ)) -> IntegrityOut:
    asset = _asset_or_404(db, media_id)
    ok, actual, detail = verify_asset(asset)
    record(db, user.username, "media.verify", ok, {"id": asset.id})
    return IntegrityOut(id=asset.id, ok=ok, expected_sha256=asset.sha256, actual_sha256=actual, detail=detail)


@router.post("/{media_id}/transcode", response_model=TranscodeJobOut, status_code=202)
def transcode(media_id: str, db: Session = Depends(get_db), user: User = Depends(_WRITE)) -> TranscodeJobOut:
    asset = _asset_or_404(db, media_id)
    job = enqueue_transcode(db, asset)
    record(db, user.username, "media.transcode", True, {"id": asset.id, "job_id": job.id})
    return _job_out(job)


@router.delete("/{media_id}", status_code=204)
def remove(media_id: str, db: Session = Depends(get_db), user: User = Depends(_WRITE)) -> None:
    asset = _asset_or_404(db, media_id)
    filename = asset.original_filename
    delete_asset(db, asset)
    record(db, user.username, "media.delete", True, {"id": media_id, "filename": filename})


def _job_out(job: TranscodeJob) -> TranscodeJobOut:
    return TranscodeJobOut(
        id=job.id,
        media_id=job.media_id,
        status=job.status,
        error=job.error,
        created_at=as_utc(job.created_at),
        finished_at=as_utc(job.finished_at) if job.finished_at else None,
    )
