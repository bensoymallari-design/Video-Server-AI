"""Store uploads, probe them, and run proxy jobs."""

from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy import delete as sql_delete
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import session_scope
from app.models import MediaAsset, TranscodeJob, utcnow
from app.services.media_inspector import (
    ALLOWED_EXTENSIONS,
    ProbeSummary,
    contained,
    probe_media,
    sha256_file,
    write_proxy,
    write_thumbnail,
)

logger = logging.getLogger(__name__)


def media_root() -> Path:
    return get_settings().resolved_media_dir()


def asset_path(asset: MediaAsset, name: str) -> Path:
    root = media_root()
    path = (root / asset.relative_dir / name).resolve()
    if not contained(path, root):
        raise HTTPException(status_code=400, detail="Invalid media path")
    return path


async def create_from_upload(db: Session, upload: UploadFile) -> tuple[MediaAsset, bool]:
    original_name = Path(upload.filename or "").name
    if not original_name:
        raise HTTPException(status_code=400, detail="The upload needs a filename")
    extension = Path(original_name).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported type {extension or '(none)'}. Allowed: {allowed}",
        )
    asset = MediaAsset(
        original_filename=original_name,
        relative_dir="pending",
        sha256="",
        size_bytes=0,
        extension=extension,
        kind="video" if extension in {".mp4", ".mov", ".mkv", ".webm"} else "image",
        validation_status="pending",
    )
    db.add(asset)
    db.flush()
    relative_dir = asset.id
    destination_dir = media_root() / relative_dir
    destination_dir.mkdir(parents=True, exist_ok=True)
    original = destination_dir / f"original{extension}"
    try:
        size, digest = await _write_limited(upload, original)
        existing = db.scalar(select(MediaAsset).where(MediaAsset.sha256 == digest, MediaAsset.id != asset.id))
        if existing is not None:
            _remove_tree(destination_dir)
            db.delete(asset)
            db.commit()
            return existing, True
        summary, raw = _inspect(original)
        thumb_ready, notes = _thumbnail(original, destination_dir / "thumbnail.jpg", summary.notes)
        (destination_dir / "probe.json").write_text(json.dumps(raw), encoding="utf-8")
        asset.relative_dir = relative_dir
        asset.sha256 = digest
        asset.size_bytes = size
        asset.kind = summary.kind
        _apply_summary(asset, summary)
        asset.thumbnail_ready = thumb_ready
        asset.validation_status = "valid"
        asset.validation_notes = notes
        db.commit()
        db.refresh(asset)
        return asset, False
    except HTTPException:
        _remove_tree(destination_dir)
        db.rollback()
        raise
    except Exception as exc:
        logger.exception("Media ingest failed")
        _remove_tree(destination_dir)
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _inspect(path: Path) -> tuple[ProbeSummary, dict]:
    try:
        return probe_media(path)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def _thumbnail(source: Path, destination: Path, notes: str) -> tuple[bool, str]:
    try:
        write_thumbnail(source, destination)
        return True, notes
    except Exception as exc:  # noqa: BLE001 - a failed thumbnail does not reject a valid file
        logger.warning("Thumbnail failed for %s: %s", source, exc)
        return False, f"{notes} Thumbnail was not created: {exc}"


def _apply_summary(asset: MediaAsset, summary: ProbeSummary) -> None:
    asset.container = summary.container
    asset.video_codec = summary.video_codec
    asset.audio_codec = summary.audio_codec
    asset.width = summary.width
    asset.height = summary.height
    asset.duration_seconds = summary.duration_seconds
    asset.frame_rate = summary.frame_rate
    asset.pixel_format = summary.pixel_format
    asset.rotation_degrees = summary.rotation_degrees


async def _write_limited(upload: UploadFile, destination: Path) -> tuple[int, str]:
    import hashlib

    limit = get_settings().max_upload_bytes
    digest = hashlib.sha256()
    size = 0
    try:
        with destination.open("wb") as handle:
            while True:
                chunk = await upload.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > limit:
                    raise HTTPException(status_code=413, detail="Upload exceeds the configured limit")
                digest.update(chunk)
                handle.write(chunk)
    except HTTPException:
        destination.unlink(missing_ok=True)
        raise
    if size == 0:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="The uploaded file is empty")
    return size, digest.hexdigest()


def verify_asset(asset: MediaAsset) -> tuple[bool, str | None, str]:
    path = asset_path(asset, f"original{asset.extension}")
    if not path.exists():
        return False, None, "Original file is missing from storage"
    actual = sha256_file(path)
    if actual != asset.sha256:
        return False, actual, "Stored bytes do not match the recorded SHA-256"
    return True, actual, "Stored bytes match the recorded SHA-256"


def delete_asset(db: Session, asset: MediaAsset) -> None:
    running = db.scalar(
        select(TranscodeJob).where(TranscodeJob.media_id == asset.id, TranscodeJob.status.in_(["queued", "running"]))
    )
    if running is not None:
        raise HTTPException(status_code=409, detail="A transcode is still running for this media")
    db.execute(sql_delete(TranscodeJob).where(TranscodeJob.media_id == asset.id))
    db.flush()
    directory = media_root() / asset.relative_dir
    if contained(directory, media_root()):
        _remove_tree(directory)
    db.delete(asset)
    db.commit()


def enqueue_transcode(db: Session, asset: MediaAsset) -> TranscodeJob:
    if asset.kind != "video":
        raise HTTPException(status_code=400, detail="Proxy transcode is for video assets")
    active = db.scalar(
        select(TranscodeJob).where(TranscodeJob.media_id == asset.id, TranscodeJob.status.in_(["queued", "running"]))
    )
    if active is not None:
        return active
    job = TranscodeJob(media_id=asset.id, status="queued")
    db.add(job)
    db.commit()
    db.refresh(job)
    thread = threading.Thread(target=_run_transcode, args=(job.id,), name=f"transcode-{job.id}", daemon=True)
    thread.start()
    return job


def _run_transcode(job_id: str) -> None:
    with session_scope() as db:
        job = db.get(TranscodeJob, job_id)
        if job is None:
            return
        asset = db.get(MediaAsset, job.media_id)
        if asset is None:
            job.status = "failed"
            job.error = "Media asset disappeared before the transcode started"
            job.finished_at = datetime.now(timezone.utc)
            db.commit()
            return
        job.status = "running"
        db.commit()
        source = asset_path(asset, f"original{asset.extension}")
        destination = asset_path(asset, "proxy.mp4")
        try:
            write_proxy(source, destination, include_audio=bool(asset.audio_codec))
        except Exception as exc:  # noqa: BLE001 - the job record is the error channel
            job.status = "failed"
            job.error = str(exc)[:2000]
            job.finished_at = utcnow()
            db.commit()
            return
        asset.has_proxy = True
        job.status = "succeeded"
        job.error = ""
        job.finished_at = utcnow()
        db.commit()


def _remove_tree(path: Path) -> None:
    if path.exists() and path.is_dir():
        for child in path.iterdir():
            if child.is_file() or child.is_symlink():
                child.unlink(missing_ok=True)
            elif child.is_dir():
                _remove_tree(child)
        path.rmdir()
