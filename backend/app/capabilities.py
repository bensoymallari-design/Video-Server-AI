"""Single source of truth for what this build can and cannot do.

The dashboard renders this list. A feature is marked available only when a
real code path implements it.
"""

from __future__ import annotations

from app.version import PHASE

CAPABILITIES: list[dict[str, object]] = [
    {
        "id": "health",
        "name": "API health",
        "phase": 1,
        "status": "available",
        "summary": "Reports process version and whether the database, FFmpeg, and FFprobe respond.",
    },
    {
        "id": "auth",
        "name": "Local authentication",
        "phase": 1,
        "status": "available",
        "summary": "Username and password sessions with admin, operator, and viewer roles.",
    },
    {
        "id": "media_upload",
        "name": "Media upload",
        "phase": 1,
        "status": "available",
        "summary": "Stores MP4, MOV, MKV, WebM, JPG, PNG, and WebP files and records a SHA-256.",
    },
    {
        "id": "media_probe",
        "name": "Media inspection",
        "phase": 1,
        "status": "available",
        "summary": "Reads resolution, frame rate, codecs, and duration with FFprobe. Files are not re-encoded on upload.",
    },
    {
        "id": "media_thumbnail",
        "name": "Thumbnails",
        "phase": 1,
        "status": "available",
        "summary": "Extracts one preview frame with FFmpeg.",
    },
    {
        "id": "media_transcode",
        "name": "Software proxy transcode",
        "phase": 1,
        "status": "available",
        "summary": "Optional libx264 proxy. This is a CPU encode, not a GPU transcode, and it does not replace the original.",
    },
    {
        "id": "display_detect",
        "name": "Display detection",
        "phase": 1,
        "status": "available",
        "summary": "Read-only. Linux uses xrandr. Windows uses the Win32 monitor APIs. Nothing writes display settings.",
    },
    {
        "id": "monitoring",
        "name": "Host monitoring",
        "phase": 1,
        "status": "available",
        "summary": "CPU, memory, disk, and display count over a WebSocket. No GPU decode counters yet.",
    },
    {
        "id": "playback",
        "name": "Native playback",
        "phase": 2,
        "status": "unavailable",
        "summary": "Fullscreen output, test patterns, and transport control are not in this build.",
    },
    {
        "id": "canvas",
        "name": "Virtual canvas editor",
        "phase": 3,
        "status": "unavailable",
        "summary": "Region mapping, layers, and saved canvases are not in this build.",
    },
    {
        "id": "profiles",
        "name": "Event profiles",
        "phase": 3,
        "status": "unavailable",
        "summary": "Profile save, load, import, and export are not in this build.",
    },
    {
        "id": "ai",
        "name": "AI orchestrator",
        "phase": 4,
        "status": "unavailable",
        "summary": "No language model is called and no tool executor is registered.",
    },
    {
        "id": "controllers",
        "name": "LED controller profiles",
        "phase": 5,
        "status": "unavailable",
        "summary": "No Colorlight or NovaStar protocol is implemented. Nothing is sent to a controller.",
    },
    {
        "id": "multi_pc",
        "name": "Multi-PC control",
        "phase": 6,
        "status": "unavailable",
        "summary": "Remote device pairing, media distribution, and scheduled start are not in this build.",
    },
    {
        "id": "installer",
        "name": "Windows installer and startup",
        "phase": 7,
        "status": "unavailable",
        "summary": "No installer, service, or logon startup entry is registered by this build.",
    },
]


def capability_payload() -> dict[str, object]:
    return {
        "current_phase": PHASE,
        "features": CAPABILITIES,
    }
