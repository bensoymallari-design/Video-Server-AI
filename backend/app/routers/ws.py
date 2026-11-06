"""Authenticated live host status."""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.database import session_scope
from app.deps import COOKIE_NAME
from app.services.accounts import user_for_token
from app.services.displays import detect_displays
from app.services.system_info import status_snapshot

logger = logging.getLogger(__name__)
router = APIRouter(tags=["monitoring"])


@router.websocket("/ws/status")
async def status_socket(websocket: WebSocket) -> None:
    with session_scope() as db:
        user = user_for_token(db, websocket.cookies.get(COOKIE_NAME))
    if user is None:
        await websocket.close(code=4401)
        return
    await websocket.accept()
    try:
        while True:
            report = detect_displays()
            connected = sum(1 for item in report.outputs if item.connected) if report.query_succeeded else None
            await websocket.send_json(status_snapshot(connected))
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        return
    except Exception:
        logger.exception("Status socket closed after an error")
        await websocket.close(code=1011)
