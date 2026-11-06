"""Deterministic desktop bounds from detected outputs."""

from __future__ import annotations

from app.schemas import DesktopBounds, DisplayOutput


def desktop_bounds(outputs: list[DisplayOutput]) -> DesktopBounds | None:
    placed = [
        item
        for item in outputs
        if item.connected
        and item.width is not None
        and item.height is not None
        and item.position_x is not None
        and item.position_y is not None
    ]
    if not placed:
        return None
    min_x = min(item.position_x for item in placed if item.position_x is not None)
    min_y = min(item.position_y for item in placed if item.position_y is not None)
    max_x = max(
        (item.position_x or 0) + (item.width or 0)
        for item in placed
    )
    max_y = max(
        (item.position_y or 0) + (item.height or 0)
        for item in placed
    )
    return DesktopBounds(x=min_x, y=min_y, width=max_x - min_x, height=max_y - min_y)


def looks_virtual(name: str) -> bool:
    upper = name.upper()
    return upper.startswith("VNC") or "VIRTUAL" in upper or upper.startswith("DEFAULT")
