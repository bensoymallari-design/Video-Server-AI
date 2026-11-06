from __future__ import annotations

import time
from pathlib import Path

import pytest

from sqlalchemy import select

from app.cli import reset_admin
from app.database import session_scope
from app.models import User
from app.security import hash_password, verify_password
from app.services.media_inspector import contained
from tests.helpers import login


def test_password_hash_round_trip() -> None:
    stored = hash_password("correct-password")
    assert verify_password("correct-password", stored) is True
    assert verify_password("other-password", stored) is False
    with pytest.raises(ValueError):
        hash_password("short")


def test_postgres_url_is_rejected() -> None:
    from app.config import Settings

    settings = Settings(
        database_url="postgresql://localhost/qubit",
        secret_key="test-secret-key",
        admin_password="test-password",
    )
    with pytest.raises(RuntimeError, match="PostgreSQL"):
        settings.resolved_database_url()


def test_health_reports_ffmpeg(client) -> None:
    body = client.get("/health").json()
    assert body["phase"] == 1
    assert body["checks"]["database"] == "ok"
    assert body["checks"]["ffmpeg"] == "ok"
    assert body["checks"]["ffprobe"] == "ok"
    assert body["status"] == "ok"


def test_login_session_and_logout(client) -> None:
    rejected = client.post("/auth/login", json={"username": "admin", "password": "wrong-password"})
    assert rejected.status_code == 401
    assert client.get("/auth/me").status_code == 401
    login(client)
    me = client.get("/auth/me")
    assert me.json() == {"username": "admin", "role": "admin"}
    assert client.post("/auth/logout").json()["status"] == "signed_out"
    assert client.get("/auth/me").status_code == 401


def test_login_rate_limit(client) -> None:
    for _ in range(8):
        assert client.post("/auth/login", json={"username": "admin", "password": "wrong-password"}).status_code == 401
    blocked = client.post("/auth/login", json={"username": "admin", "password": "wrong-password"})
    assert blocked.status_code == 429


def test_protected_routes_require_authentication(client) -> None:
    assert client.get("/displays").status_code == 401
    assert client.get("/media").status_code == 401
    assert client.get("/system/host").status_code == 401


def test_capabilities_mark_later_phases_unavailable(client) -> None:
    login(client)
    features = {item["id"]: item for item in client.get("/system/capabilities").json()["features"]}
    assert features["media_probe"]["status"] == "available"
    assert features["playback"]["status"] == "unavailable"
    assert features["ai"]["status"] == "unavailable"
    assert features["controllers"]["status"] == "unavailable"
    assert features["multi_pc"]["status"] == "unavailable"


def test_host_and_config(client) -> None:
    login(client)
    host = client.get("/system/host").json()
    assert host["phase"] == 1
    assert host["cpu_count"] >= 1
    assert host["memory_total_bytes"] > 0
    assert "note" in host["gpu"]
    config = client.get("/system/config").json()
    assert config["localhost_only"] is True
    assert config["database"] == "sqlite"
    assert "secret" not in config


def test_viewer_cannot_upload_or_read_config(client) -> None:
    with session_scope() as db:
        if db.scalar(select(User).where(User.username == "viewer")) is None:
            db.add(User(username="viewer", password_hash=hash_password("viewer-password"), role="viewer"))
            db.commit()
    login(client, "viewer", "viewer-password")
    assert client.get("/media").status_code == 200
    upload = client.post("/media", files={"file": ("clip.mp4", b"nope", "video/mp4")})
    assert upload.status_code == 403
    assert client.get("/system/config").status_code == 403
    assert client.get("/system/audit").status_code == 403


def test_reset_admin_replaces_the_password(client) -> None:
    try:
        reset_admin("admin", "replaced-password")
        assert client.post("/auth/login", json={"username": "admin", "password": "test-password"}).status_code == 401
        login(client, "admin", "replaced-password")
    finally:
        reset_admin("admin", "test-password")


def test_audit_records_login(client) -> None:
    login(client)
    rows = client.get("/system/audit").json()
    assert any(row["action"] == "auth.login" and row["success"] is True for row in rows)


def test_status_socket_requires_a_session_and_emits_a_sample(client) -> None:
    with pytest.raises(Exception):
        with client.websocket_connect("/ws/status") as socket:
            socket.receive_json()
    login(client)
    with client.websocket_connect("/ws/status") as socket:
        sample = socket.receive_json()
    assert sample["type"] == "status"
    assert "cpu_percent" in sample
    assert "memory_total_bytes" in sample


def test_contained_rejects_paths_outside_the_media_root(tmp_path: Path) -> None:
    root = tmp_path / "media"
    root.mkdir()
    assert contained(root / "asset" / "original.mp4", root) is True
    assert contained(tmp_path / "other.txt", root) is False
