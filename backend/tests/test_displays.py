from __future__ import annotations

import sys
from pathlib import Path

import pytest

from app.services.displays.geometry import desktop_bounds, looks_virtual
from app.services.displays.xrandr import parse_xrandr
from tests.helpers import login

FIXTURE = Path(__file__).parent / "fixtures" / "xrandr_wall.txt"


def test_xrandr_wall_parser_reads_geometry_rotation_and_modes() -> None:
    outputs = parse_xrandr(FIXTURE.read_text(encoding="utf-8"))
    by_name = {item.name: item for item in outputs}
    assert set(by_name) == {"DP-0", "DP-2", "HDMI-0", "HDMI-1", "HDMI-2"}

    primary = by_name["DP-0"]
    assert primary.connected is True
    assert primary.primary is True
    assert (primary.width, primary.height, primary.position_x, primary.position_y) == (3840, 2160, 0, 0)
    assert primary.refresh_hz == 60.0
    assert primary.rotation == "normal"
    assert primary.physical_width_mm == 600
    current = [mode for mode in primary.modes if mode.current]
    assert len(current) == 1
    assert current[0].preferred is True
    assert len(primary.modes) == 5

    portrait = by_name["HDMI-1"]
    assert portrait.rotation == "left"
    assert (portrait.width, portrait.height) == (1080, 1920)
    assert portrait.position_x == 7680
    assert portrait.refresh_hz == 60.0
    assert any(mode.preferred and not mode.current for mode in portrait.modes)

    assert by_name["HDMI-0"].connected is False
    assert by_name["HDMI-0"].width is None

    negative = by_name["HDMI-2"]
    assert (negative.position_x, negative.position_y) == (-1920, -120)


def test_desktop_bounds_include_negative_origin() -> None:
    outputs = parse_xrandr(FIXTURE.read_text(encoding="utf-8"))
    bounds = desktop_bounds(outputs)
    assert bounds is not None
    assert bounds.x == -1920
    assert bounds.y == -120
    assert bounds.width == 7680 + 1080 + 1920
    assert bounds.height == 120 + 2160


def test_xrandr_parser_accepts_glued_negative_signs() -> None:
    output = parse_xrandr("HDMI-2 connected 1920x1080+-1920+-80\n")[0]
    assert (output.position_x, output.position_y) == (-1920, -80)


def test_xrandr_parser_ignores_blank_and_garbage() -> None:
    assert parse_xrandr("") == []
    assert parse_xrandr("Screen 0: current 1920 x 1080\nnot a display\n") == []


def test_virtual_output_names() -> None:
    assert looks_virtual("VNC-0") is True
    assert looks_virtual("VIRTUAL1") is True
    assert looks_virtual("DP-0") is False


def test_windows_detector_refuses_to_run_off_windows() -> None:
    from app.services.displays.windows import detect_windows

    if sys.platform == "win32":
        pytest.skip("Windows host would query real monitors")
    with pytest.raises(RuntimeError):
        detect_windows()


def test_display_endpoint_reports_the_query_result(client) -> None:
    login(client)
    body = client.get("/displays").json()
    assert body["adapter"] in {"linux-xrandr", "windows-user32", "unavailable"}
    assert body["limitations"]
    assert body["note"]
    assert isinstance(body["outputs"], list)
    if body["query_succeeded"]:
        assert body["error"] is None
    else:
        assert body["outputs"] == []
        assert body["error"]
    text = Path(__file__).parents[1].joinpath("app/services/displays/windows.py").read_text(encoding="utf-8")
    assert "ChangeDisplaySettingsW" not in text
    assert "ChangeDisplaySettingsExW" not in text
