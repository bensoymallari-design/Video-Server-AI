"""Test environment. Environment variables are set before the application is imported."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Generator
from pathlib import Path

_ROOT = Path(tempfile.mkdtemp(prefix="qubit-pytest-"))
os.environ["QUBIT_SECRET_KEY"] = "test-secret-key"
os.environ["QUBIT_ADMIN_USERNAME"] = "admin"
os.environ["QUBIT_ADMIN_PASSWORD"] = "test-password"
os.environ["QUBIT_DATABASE_URL"] = "sqlite:///" + (_ROOT / "test.db").as_posix()
os.environ["QUBIT_MEDIA_DIR"] = str(_ROOT / "media")
os.environ["QUBIT_DATA_DIR"] = str(_ROOT)
os.environ["QUBIT_HOST"] = "127.0.0.1"
os.environ["QUBIT_LOG_LEVEL"] = "WARNING"
os.environ["QUBIT_MAX_UPLOAD_BYTES"] = str(8 * 1024 * 1024)

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.security import login_attempts


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    login_attempts.clear()
    with TestClient(app) as test_client:
        yield test_client
    login_attempts.clear()

