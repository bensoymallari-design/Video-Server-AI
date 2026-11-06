"""Host, GPU, and live resource snapshots.

GPU queries use fixed commands. They are not built from user or model text.
"""

from __future__ import annotations

import json
import platform
import subprocess
import sys
import time
from pathlib import Path

import psutil

from app.config import get_settings
from app.schemas import GpuAdapter, GpuReport, HostReport
from app.version import PHASE, __version__

_STARTED = time.time()


def host_report() -> HostReport:
    settings = get_settings()
    memory = psutil.virtual_memory()
    return HostReport(
        hostname=platform.node(),
        platform=platform.system(),
        platform_version=platform.platform(),
        python_version=platform.python_version(),
        cpu_count=os_cpu_count(),
        memory_total_bytes=int(memory.total),
        memory_available_bytes=int(memory.available),
        gpu=gpu_report(),
        localhost_only=settings.localhost_only,
        app_version=__version__,
        phase=PHASE,
    )


def os_cpu_count() -> int | None:
    import os

    return os.cpu_count()


def gpu_report() -> GpuReport:
    if sys.platform == "win32":
        return _gpu_windows()
    if sys.platform.startswith("linux"):
        return _gpu_linux()
    return GpuReport(
        available=False,
        adapters=[],
        note=f"GPU detection is not implemented for {sys.platform}.",
    )


def _gpu_linux() -> GpuReport:
    try:
        completed = subprocess.run(
            ["lspci", "-mm"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except FileNotFoundError:
        return GpuReport(
            available=False,
            adapters=[],
            note="lspci is not installed, so this host did not report a PCI display adapter.",
        )
    except subprocess.TimeoutExpired:
        return GpuReport(available=False, adapters=[], note="lspci timed out.")
    adapters: list[GpuAdapter] = []
    if completed.returncode == 0:
        for line in completed.stdout.splitlines():
            lower = line.lower()
            if "vga" in lower or "3d" in lower or "display" in lower:
                adapters.append(GpuAdapter(name=line.strip(), source="lspci"))
    nvidia = Path("/proc/driver/nvidia/gpus")
    if nvidia.exists():
        for child in nvidia.iterdir():
            adapters.append(GpuAdapter(name=child.name, source="nvidia-proc"))
    if not adapters:
        return GpuReport(
            available=False,
            adapters=[],
            note="No PCI display adapter was reported. Hardware decode and GPU output are unverified on this machine.",
        )
    return GpuReport(
        available=True,
        adapters=adapters,
        note="Adapter names come from a read-only PCI query. This is not a measure of decode or display performance.",
    )


def _gpu_windows() -> GpuReport:
    script = (
        "Get-CimInstance -ClassName Win32_VideoController | "
        "Select-Object Name,DriverVersion | ConvertTo-Json -Compress"
    )
    try:
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return GpuReport(available=False, adapters=[], note=f"GPU query failed: {exc}")
    if completed.returncode != 0 or not completed.stdout.strip():
        message = (completed.stderr or "Win32_VideoController returned no data").strip()
        return GpuReport(available=False, adapters=[], note=message[:500])
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return GpuReport(available=False, adapters=[], note="GPU query returned data that was not JSON.")
    rows = payload if isinstance(payload, list) else [payload]
    adapters = [
        GpuAdapter(name=str(row.get("Name") or "Unknown display adapter"), source="Win32_VideoController")
        for row in rows
        if isinstance(row, dict)
    ]
    return GpuReport(
        available=bool(adapters),
        adapters=adapters,
        note="Adapter names come from Win32_VideoController. Decode capability was not measured.",
    )


def status_snapshot(display_count: int | None) -> dict[str, object]:
    memory = psutil.virtual_memory()
    root = get_settings().resolved_data_dir()
    disk = psutil.disk_usage(str(root))
    return {
        "type": "status",
        "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "uptime_seconds": round(time.time() - _STARTED, 1),
        "cpu_percent": psutil.cpu_percent(interval=None),
        "memory_percent": memory.percent,
        "memory_used_bytes": int(memory.used),
        "memory_total_bytes": int(memory.total),
        "disk_percent": disk.percent,
        "disk_used_bytes": int(disk.used),
        "disk_total_bytes": int(disk.total),
        "displays_connected": display_count,
    }
