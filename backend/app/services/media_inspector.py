"""FFprobe inspection and FFmpeg thumbnail / proxy helpers.

Cropping and mapping are not done here. Upload stores the original file.
A proxy is created only when an operator asks for one.
"""

from __future__ import annotations

import hashlib
import json
import logging
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_EXTENSIONS = VIDEO_EXTENSIONS | IMAGE_EXTENSIONS


@dataclass
class ProbeSummary:
    container: str | None
    video_codec: str | None
    audio_codec: str | None
    width: int | None
    height: int | None
    duration_seconds: float | None
    frame_rate: float | None
    pixel_format: str | None
    rotation_degrees: int | None
    kind: str
    notes: str


def tool_available(name: str) -> bool:
    return shutil.which(name) is not None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def probe_media(path: Path) -> tuple[ProbeSummary, dict]:
    if not tool_available("ffprobe"):
        raise RuntimeError("ffprobe is not installed")
    completed = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(path),
        ],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if completed.returncode != 0:
        message = (completed.stderr or "ffprobe failed").strip()
        raise ValueError(message[:2000])
    payload = json.loads(completed.stdout or "{}")
    return _summarize(payload), payload


def _summarize(payload: dict) -> ProbeSummary:
    streams = payload.get("streams") or []
    video = next((item for item in streams if item.get("codec_type") == "video"), None)
    audio = next((item for item in streams if item.get("codec_type") == "audio"), None)
    if video is None:
        raise ValueError("The file has no video or image stream")
    fmt = payload.get("format") or {}
    duration = _float_or_none(fmt.get("duration"))
    rotation = _rotation(video)
    codec = video.get("codec_name")
    kind = "image" if _is_image(codec, duration) else "video"
    return ProbeSummary(
        container=fmt.get("format_name"),
        video_codec=codec,
        audio_codec=audio.get("codec_name") if audio else None,
        width=_int_or_none(video.get("width")),
        height=_int_or_none(video.get("height")),
        duration_seconds=duration,
        frame_rate=_fraction(video.get("avg_frame_rate")),
        pixel_format=video.get("pix_fmt"),
        rotation_degrees=rotation,
        kind=kind,
        notes="Original file was stored without re-encoding.",
    )


def _is_image(codec: str | None, duration: float | None) -> bool:
    if codec in {"png", "mjpeg", "webp", "jpeg", "bmp", "gif"} and (duration is None or duration <= 0.05):
        return True
    return False


def _rotation(stream: dict) -> int | None:
    tags = stream.get("tags") or {}
    raw = tags.get("rotate")
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _fraction(value: object) -> float | None:
    if not isinstance(value, str) or value in {"0/0", "N/A", ""}:
        return None
    if "/" in value:
        numerator, denominator = value.split("/", 1)
        try:
            denom = float(denominator)
            if denom == 0:
                return None
            return float(numerator) / denom
        except ValueError:
            return None
    try:
        return float(value)
    except ValueError:
        return None


def _float_or_none(value: object) -> float | None:
    if value in (None, "N/A", ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_or_none(value: object) -> int | None:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def write_thumbnail(source: Path, destination: Path) -> None:
    if not tool_available("ffmpeg"):
        raise RuntimeError("ffmpeg is not installed")
    destination.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(source),
            "-frames:v",
            "1",
            "-vf",
            "scale=480:-1",
            str(destination),
        ],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if completed.returncode != 0 or not destination.exists() or destination.stat().st_size == 0:
        destination.unlink(missing_ok=True)
        message = (completed.stderr or "thumbnail extraction failed").strip()
        raise RuntimeError(message[:2000])


def write_proxy(source: Path, destination: Path, include_audio: bool) -> None:
    if not tool_available("ffmpeg"):
        raise RuntimeError("ffmpeg is not installed")
    destination.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(source),
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "20",
        "-pix_fmt",
        "yuv420p",
    ]
    if include_audio:
        command.extend(["-c:a", "aac", "-b:a", "128k"])
    else:
        command.append("-an")
    command.extend(["-movflags", "+faststart", str(destination)])
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )
    if completed.returncode != 0 or not destination.exists() or destination.stat().st_size == 0:
        destination.unlink(missing_ok=True)
        message = (completed.stderr or "transcode failed").strip()
        raise RuntimeError(message[:2000])
    probe_media(destination)


def contained(path: Path, root: Path) -> bool:
    resolved = path.resolve()
    base = root.resolve()
    return resolved == base or base in resolved.parents
