"""Choose the display detector for the current operating system."""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone

from app.schemas import DisplayReport

logger = logging.getLogger(__name__)

_LIMITATIONS = [
    "No display detector is available for this operating system.",
    "An empty list means the query did not run. It is not a claim that zero panels are attached.",
]


def detect_displays() -> DisplayReport:
    try:
        if sys.platform == "win32":
            from app.services.displays.windows import detect_windows

            return detect_windows()
        if sys.platform.startswith("linux"):
            from app.services.displays.linux import detect_linux

            return detect_linux()
        return _unavailable(f"No display detector is implemented for {sys.platform}")
    except Exception as exc:  # noqa: BLE001 - detector failures must not take down the API
        logger.exception("Display detection failed")
        return _unavailable(str(exc))


def _unavailable(message: str) -> DisplayReport:
    return DisplayReport(
        platform=sys.platform,
        adapter="unavailable",
        query_succeeded=False,
        virtual_output_suspected=False,
        captured_at=datetime.now(timezone.utc),
        note="Display detection is unavailable. No outputs were invented.",
        error=message,
        limitations=list(_LIMITATIONS),
        outputs=[],
    )
