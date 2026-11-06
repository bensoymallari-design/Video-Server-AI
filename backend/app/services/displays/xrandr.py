"""Parse `xrandr --query` text into display outputs.

The parenthetical rotation list in xrandr is the set of supported rotations.
The active rotation, when not normal, is the word that appears before that
parenthesis.
"""

from __future__ import annotations

import re

from app.schemas import DisplayOutput, VideoMode

_OUTPUT_RE = re.compile(r"^(?P<name>\S+)\s+(?P<state>connected|disconnected)(?P<rest>.*)$")
# xrandr prints geometry with printf "%dx%d%+d%+d". Negative origins look like
# 1920x1080-1920-120. Some reports also glue the signs as +-1920.
_GEOM_RE = re.compile(r"(?P<w>\d+)x(?P<h>\d+)(?P<x>[+-]-?\d+)(?P<y>[+-]-?\d+)")
_ROTATION_RE = re.compile(r"\b(normal|left|inverted|right)\b")
_MM_RE = re.compile(r"(?P<w>\d+)mm x (?P<h>\d+)mm")
_MODE_RE = re.compile(r"^\s{2,}(?P<w>\d+)x(?P<h>\d+)\s+(?P<rates>.+)$")
_RATE_RE = re.compile(r"(?P<hz>\d+(?:\.\d+)?)(?P<flags>[*+]*)")


def parse_xrandr(text: str) -> list[DisplayOutput]:
    outputs: list[DisplayOutput] = []
    current: DisplayOutput | None = None
    for line in text.splitlines():
        if line.startswith((" ", "\t")):
            if current is not None:
                _append_modes(current, line)
            continue
        match = _OUTPUT_RE.match(line.strip())
        if match is None:
            current = None
            continue
        current = _output_from_header(match.group("name"), match.group("state"), match.group("rest"))
        outputs.append(current)
    _unique_ids(outputs)
    return outputs


def _output_from_header(name: str, state: str, rest: str) -> DisplayOutput:
    geometry = _GEOM_RE.search(rest)
    physical = _MM_RE.search(rest)
    width = height = position_x = position_y = None
    if geometry is not None:
        width = int(geometry.group("w"))
        height = int(geometry.group("h"))
        position_x = _coordinate(geometry.group("x"))
        position_y = _coordinate(geometry.group("y"))
    return DisplayOutput(
        id=name,
        name=name,
        connector=name,
        connected=state == "connected",
        primary=bool(re.search(r"\bprimary\b", rest)),
        width=width,
        height=height,
        position_x=position_x,
        position_y=position_y,
        rotation=_rotation(rest),
        physical_width_mm=int(physical.group("w")) if physical else None,
        physical_height_mm=int(physical.group("h")) if physical else None,
        modes=[],
    )


def _coordinate(value: str) -> int:
    if value.startswith("+-"):
        return -int(value[2:])
    if value.startswith("-+"):
        return int(value[2:])
    return int(value)


def _rotation(rest: str) -> str:
    head = rest.split("(", 1)[0]
    match = _ROTATION_RE.search(head)
    if match is None or match.group(1) == "normal":
        return "normal"
    return match.group(1)


def _append_modes(output: DisplayOutput, line: str) -> None:
    match = _MODE_RE.match(line)
    if match is None:
        return
    width = int(match.group("w"))
    height = int(match.group("h"))
    for rate in _RATE_RE.finditer(match.group("rates")):
        flags = rate.group("flags")
        output.modes.append(
            VideoMode(
                width=width,
                height=height,
                refresh_hz=float(rate.group("hz")),
                current="*" in flags,
                preferred="+" in flags,
            )
        )
    starred = next((mode for mode in output.modes if mode.current), None)
    if starred is not None:
        output.refresh_hz = starred.refresh_hz


def _unique_ids(outputs: list[DisplayOutput]) -> None:
    seen: dict[str, int] = {}
    for output in outputs:
        count = seen.get(output.id, 0) + 1
        seen[output.id] = count
        if count > 1:
            output.id = f"{output.name}-{count}"
