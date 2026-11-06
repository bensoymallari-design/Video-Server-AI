"""Runtime configuration.

Values come from the process environment, then from a `.env` file at the
repository root. Secrets have no defaults that would be safe to ship.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent


class Settings(BaseSettings):
    app_name: str = "Qubit AI Media Server"
    host: str = "127.0.0.1"
    port: int = 8000
    log_level: str = "INFO"
    secret_key: str = ""
    admin_username: str = "admin"
    admin_password: str = ""
    token_ttl_hours: int = 12
    max_upload_bytes: int = 2_147_483_648
    cors_origins: str = "http://127.0.0.1:3000,http://localhost:3000"
    database_url: str = "sqlite:///./data/qubit.db"
    media_dir: str = "./data/media"
    data_dir: str = "./data"

    model_config = SettingsConfigDict(
        env_prefix="QUBIT_",
        env_file=(REPO_ROOT / ".env", BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("admin_username")
    @classmethod
    def username_not_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("admin username cannot be blank")
        return cleaned

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def localhost_only(self) -> bool:
        return self.host in {"127.0.0.1", "localhost", "::1"}

    def resolved_data_dir(self) -> Path:
        return _resolve_dir(self.data_dir)

    def resolved_media_dir(self) -> Path:
        return _resolve_dir(self.media_dir)

    def resolved_database_url(self) -> str:
        url = self.database_url
        if url.startswith("postgres://") or url.startswith("postgresql"):
            raise RuntimeError(
                "PostgreSQL is reserved for a later phase. The driver is not installed. "
                "Use a sqlite:/// URL."
            )
        if not url.startswith("sqlite:///"):
            raise RuntimeError(f"Unsupported database URL scheme: {url.split(':', 1)[0]}")
        raw = url[len("sqlite:///") :]
        if raw == ":memory:":
            return "sqlite:///:memory:"
        path = Path(raw)
        if not path.is_absolute():
            path = (BACKEND_ROOT / path).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        return "sqlite:///" + path.as_posix()


def _resolve_dir(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = (BACKEND_ROOT / path).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


@lru_cache
def get_settings() -> Settings:
    return Settings()


def clear_settings_cache() -> None:
    get_settings.cache_clear()
