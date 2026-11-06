"""Linux display detection through xrandr.

This reads the running X server. It does not call xrandr --output and does
not change the desktop.
"""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone

from app.schemas import DisplayReport
from app.services.displays.geometry import desktop_bounds, looks_virtual
from app.services.displays.xrandr import parse_xrandr

_LIMITATIONS = [
    "Detection is read-only.",
    "The refresh rate is the mode xrandr marks current, not a measured signal.",
    "No LED processor, sending card, or receiving card is queried.",
    "xrandr describes the X desktop. A virtual VNC output is not a GPU HDMI port.",
]


def detect_linux() -> DisplayReport:
    if not sys.platform.startswith("linux"):
        raise RuntimeError("The xrandr detector only runs on Linux")
    try:
        completed = subprocess.run(
            ["xrandr", "--query"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except FileNotFoundError:
        return _failed("xrandr is not installed")
    except subprocess.TimeoutExpired:
        return _failed("xrandr did not answer within 5 seconds")
    if completed.returncode != 0:
        message = (completed.stderr or completed.stdout or "xrandr failed").strip()
        return _failed(message)
    outputs = parse_xrandr(completed.stdout)
    connected = [item for item in outputs if item.connected]
    virtual = any(looks_virtual(item.name) for item in connected)
    note = (
        "Read-only xrandr query. A connector name such as VNC or VIRTUAL is a virtual desktop, "
        "not confirmation of a physical panel or LED processor."
    )
    if virtual:
        note += " This host reported a virtual output."
    elif not connected:
        note += " No connected output was reported."
    return DisplayReport(
        platform="linux",
        adapter="linux-xrandr",
        query_succeeded=True,
        virtual_output_suspected=virtual,
        captured_at=datetime.now(timezone.utc),
        note=note,
        error=None,
        limitations=list(_LIMITATIONS),
        desktop=desktop_bounds(outputs),
        outputs=outputs,
    )


def _failed(message: str) -> DisplayReport:
    return DisplayReport(
        platform="linux",
        adapter="linux-xrandr",
        query_succeeded=False,
        virtual_output_suspected=False,
        captured_at=datetime.now(timezone.utc),
        note="Display detection did not complete. No display list is invented when the query fails.",
        error=message,
        limitations=list(_LIMITATIONS),
        outputs=[],
    )
