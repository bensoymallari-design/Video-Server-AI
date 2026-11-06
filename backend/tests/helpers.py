"""Shared HTTP helpers for API tests."""

from __future__ import annotations

from fastapi.testclient import TestClient


def login(client: TestClient, username: str = "admin", password: str = "test-password") -> None:
    response = client.post("/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
