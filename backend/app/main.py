"""Qubit AI Media Server API."""

from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db, session_scope
from app.logging_config import configure_logging
from app.routers import auth, displays, health, media, system, ws
from app.services.accounts import ensure_admin
from app.services.system_info import status_snapshot
from app.version import __version__

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    if not settings.localhost_only:
        logger.warning("QUBIT_HOST is %s. The API is not bound to loopback.", settings.host)
    if not settings.secret_key:
        logger.warning("QUBIT_SECRET_KEY is empty. Set a persistent secret before sharing this host.")
    init_db()
    with session_scope() as db:
        ensure_admin(db, settings)
    status_snapshot(None)
    logger.info("%s %s listening for application startup", settings.app_name, __version__)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    application = FastAPI(
        title=settings.app_name,
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url=None,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Content-Type", "X-Request-ID"],
    )

    @application.middleware("http")
    async def request_log(request: Request, call_next):  # type: ignore[no-untyped-def]
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        started = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - started) * 1000
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "%s %s %s %.1fms request_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
            request_id,
        )
        return response

    application.include_router(health.router)
    application.include_router(auth.router)
    application.include_router(displays.router)
    application.include_router(media.router)
    application.include_router(system.router)
    application.include_router(ws.router)
    return application


app = create_app()
