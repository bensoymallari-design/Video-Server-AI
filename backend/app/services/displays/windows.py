"""Windows display detection through user32.

Geometry comes from EnumDisplayMonitors and GetMonitorInfoW. The active mode
and the mode list come from EnumDisplaySettingsW. This module never calls
ChangeDisplaySettings.

The Phase 1 development host is Linux, so this path is implemented and
import-safe here, and it is not executed by the test suite.
"""

from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes
from datetime import datetime, timezone

from app.schemas import DisplayOutput, DisplayReport, VideoMode
from app.services.displays.geometry import desktop_bounds

ENUM_CURRENT_SETTINGS = 0xFFFFFFFF
DISPLAY_DEVICE_ACTIVE = 0x00000001
DISPLAY_DEVICE_PRIMARY_DEVICE = 0x00000004
DMDO_DEFAULT = 0
DMDO_90 = 1
DMDO_180 = 2
DMDO_270 = 3

_ROTATION = {
    DMDO_DEFAULT: "normal",
    DMDO_90: "left",
    DMDO_180: "inverted",
    DMDO_270: "right",
}

_LIMITATIONS = [
    "Detection is read-only. ChangeDisplaySettings is not called.",
    "The refresh rate is the current DEVMODE frequency, not a measured signal.",
    "Preferred modes are not identified. Windows enumeration does not mark a preferred mode the way xrandr does.",
    "No LED processor, sending card, or receiving card is queried.",
    "This Windows path was not executed on physical display hardware by the Phase 1 Linux test run.",
]


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG),
    ]


class MONITORINFOEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", wintypes.DWORD),
        ("szDevice", wintypes.WCHAR * 32),
    ]


class POINTL(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


class DEVMODEW(ctypes.Structure):
    """Display-oriented DEVMODEW. The position union overlays the printer fields."""

    _fields_ = [
        ("dmDeviceName", wintypes.WCHAR * 32),
        ("dmSpecVersion", wintypes.WORD),
        ("dmDriverVersion", wintypes.WORD),
        ("dmSize", wintypes.WORD),
        ("dmDriverExtra", wintypes.WORD),
        ("dmFields", wintypes.DWORD),
        ("dmPosition", POINTL),
        ("dmDisplayOrientation", wintypes.DWORD),
        ("dmDisplayFixedOutput", wintypes.DWORD),
        ("dmColor", wintypes.SHORT),
        ("dmDuplex", wintypes.SHORT),
        ("dmYResolution", wintypes.SHORT),
        ("dmTTOption", wintypes.SHORT),
        ("dmCollate", wintypes.SHORT),
        ("dmFormName", wintypes.WCHAR * 32),
        ("dmLogPixels", wintypes.WORD),
        ("dmBitsPerPel", wintypes.DWORD),
        ("dmPelsWidth", wintypes.DWORD),
        ("dmPelsHeight", wintypes.DWORD),
        ("dmDisplayFlags", wintypes.DWORD),
        ("dmDisplayFrequency", wintypes.DWORD),
        ("dmICMMethod", wintypes.DWORD),
        ("dmICMIntent", wintypes.DWORD),
        ("dmMediaType", wintypes.DWORD),
        ("dmDitherType", wintypes.DWORD),
        ("dmReserved1", wintypes.DWORD),
        ("dmReserved2", wintypes.DWORD),
        ("dmPanningWidth", wintypes.DWORD),
        ("dmPanningHeight", wintypes.DWORD),
    ]


class DISPLAY_DEVICEW(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("DeviceName", wintypes.WCHAR * 32),
        ("DeviceString", wintypes.WCHAR * 128),
        ("StateFlags", wintypes.DWORD),
        ("DeviceID", wintypes.WCHAR * 128),
        ("DeviceKey", wintypes.WCHAR * 128),
    ]


def detect_windows() -> DisplayReport:
    if sys.platform != "win32":
        raise RuntimeError("The Win32 display detector only runs on Windows")
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    _bind_signatures(user32)
    monitors = _monitors(user32)
    outputs = _devices(user32, monitors)
    return DisplayReport(
        platform="windows",
        adapter="windows-user32",
        query_succeeded=True,
        virtual_output_suspected=False,
        captured_at=datetime.now(timezone.utc),
        note=(
            "Read-only Win32 enumeration through EnumDisplayMonitors and EnumDisplaySettings. "
            "This does not confirm an LED processor lock, and it does not change the desktop."
        ),
        limitations=list(_LIMITATIONS),
        desktop=desktop_bounds(outputs),
        outputs=outputs,
    )


def _bind_signatures(user32: ctypes.WinDLL) -> None:
    monitor_enum = ctypes.WINFUNCTYPE(
        wintypes.BOOL,
        wintypes.HMONITOR,
        wintypes.HDC,
        ctypes.POINTER(RECT),
        wintypes.LPARAM,
    )
    user32.EnumDisplayMonitors.argtypes = [wintypes.HDC, ctypes.POINTER(RECT), monitor_enum, wintypes.LPARAM]
    user32.EnumDisplayMonitors.restype = wintypes.BOOL
    user32.GetMonitorInfoW.argtypes = [wintypes.HMONITOR, ctypes.POINTER(MONITORINFOEXW)]
    user32.GetMonitorInfoW.restype = wintypes.BOOL
    user32.EnumDisplayDevicesW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        ctypes.POINTER(DISPLAY_DEVICEW),
        wintypes.DWORD,
    ]
    user32.EnumDisplayDevicesW.restype = wintypes.BOOL
    user32.EnumDisplaySettingsW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        ctypes.POINTER(DEVMODEW),
    ]
    user32.EnumDisplaySettingsW.restype = wintypes.BOOL


def _monitors(user32: ctypes.WinDLL) -> dict[str, MONITORINFOEXW]:
    found: dict[str, MONITORINFOEXW] = {}

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HMONITOR, wintypes.HDC, ctypes.POINTER(RECT), wintypes.LPARAM)
    def callback(hmonitor, _hdc, _rect, _data):  # type: ignore[no-untyped-def]
        info = MONITORINFOEXW()
        info.cbSize = ctypes.sizeof(MONITORINFOEXW)
        if user32.GetMonitorInfoW(hmonitor, ctypes.byref(info)):
            found[str(info.szDevice)] = info
        return True

    if not user32.EnumDisplayMonitors(None, None, callback, 0):
        raise OSError("EnumDisplayMonitors failed")
    return found


def _devices(user32: ctypes.WinDLL, monitors: dict[str, MONITORINFOEXW]) -> list[DisplayOutput]:
    outputs: list[DisplayOutput] = []
    index = 0
    while True:
        device = DISPLAY_DEVICEW()
        device.cb = ctypes.sizeof(DISPLAY_DEVICEW)
        if not user32.EnumDisplayDevicesW(None, index, ctypes.byref(device), 0):
            break
        index += 1
        if not (device.StateFlags & DISPLAY_DEVICE_ACTIVE):
            continue
        name = str(device.DeviceName)
        current = _mode(user32, name, ENUM_CURRENT_SETTINGS)
        modes = _mode_list(user32, name, current)
        monitor = monitors.get(name)
        position_x = position_y = width = height = None
        primary = bool(device.StateFlags & DISPLAY_DEVICE_PRIMARY_DEVICE)
        if monitor is not None:
            rect = monitor.rcMonitor
            position_x = int(rect.left)
            position_y = int(rect.top)
            width = int(rect.right - rect.left)
            height = int(rect.bottom - rect.top)
            primary = primary or bool(monitor.dwFlags & 1)
        elif current is not None:
            width = int(current.dmPelsWidth)
            height = int(current.dmPelsHeight)
        refresh = float(current.dmDisplayFrequency) if current is not None and current.dmDisplayFrequency else None
        rotation = _ROTATION.get(int(current.dmDisplayOrientation), "normal") if current is not None else "normal"
        label = str(device.DeviceString).strip() or name
        outputs.append(
            DisplayOutput(
                id=name,
                name=label,
                connector=name,
                connected=True,
                primary=primary,
                width=width,
                height=height,
                position_x=position_x,
                position_y=position_y,
                refresh_hz=refresh,
                rotation=rotation,
                modes=modes,
            )
        )
    return outputs


def _blank_mode() -> DEVMODEW:
    mode = DEVMODEW()
    mode.dmSize = ctypes.sizeof(DEVMODEW)
    return mode


def _mode(user32: ctypes.WinDLL, device_name: str, mode_index: int) -> DEVMODEW | None:
    mode = _blank_mode()
    if not user32.EnumDisplaySettingsW(device_name, mode_index, ctypes.byref(mode)):
        return None
    return mode


def _mode_list(user32: ctypes.WinDLL, device_name: str, current: DEVMODEW | None) -> list[VideoMode]:
    modes: list[VideoMode] = []
    seen: set[tuple[int, int, int]] = set()
    index = 0
    while True:
        mode = _mode(user32, device_name, index)
        if mode is None:
            break
        index += 1
        width = int(mode.dmPelsWidth)
        height = int(mode.dmPelsHeight)
        refresh = int(mode.dmDisplayFrequency)
        if width <= 0 or height <= 0 or refresh <= 0:
            continue
        key = (width, height, refresh)
        if key in seen:
            continue
        seen.add(key)
        is_current = (
            current is not None
            and int(current.dmPelsWidth) == width
            and int(current.dmPelsHeight) == height
            and int(current.dmDisplayFrequency) == refresh
        )
        modes.append(
            VideoMode(
                width=width,
                height=height,
                refresh_hz=float(refresh),
                current=is_current,
                preferred=False,
            )
        )
    return modes
