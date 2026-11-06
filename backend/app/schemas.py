"""API and display-detection models."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class UserOut(BaseModel):
    username: str
    role: str


class VideoMode(BaseModel):
    width: int
    height: int
    refresh_hz: float
    current: bool = False
    preferred: bool = False


class DisplayOutput(BaseModel):
    id: str
    name: str
    connector: str
    connected: bool
    primary: bool = False
    width: int | None = None
    height: int | None = None
    position_x: int | None = None
    position_y: int | None = None
    refresh_hz: float | None = None
    rotation: str = "normal"
    physical_width_mm: int | None = None
    physical_height_mm: int | None = None
    modes: list[VideoMode] = Field(default_factory=list)


class DesktopBounds(BaseModel):
    x: int
    y: int
    width: int
    height: int


class DisplayReport(BaseModel):
    platform: str
    adapter: str
    query_succeeded: bool
    virtual_output_suspected: bool
    captured_at: datetime
    note: str
    error: str | None = None
    limitations: list[str] = Field(default_factory=list)
    desktop: DesktopBounds | None = None
    outputs: list[DisplayOutput] = Field(default_factory=list)


class GpuAdapter(BaseModel):
    name: str
    source: str


class GpuReport(BaseModel):
    available: bool
    adapters: list[GpuAdapter] = Field(default_factory=list)
    note: str


class HostReport(BaseModel):
    hostname: str
    platform: str
    platform_version: str
    python_version: str
    cpu_count: int | None
    memory_total_bytes: int
    memory_available_bytes: int
    gpu: GpuReport
    localhost_only: bool
    app_version: str
    phase: int


class ConfigReport(BaseModel):
    app_name: str
    version: str
    phase: int
    host: str
    port: int
    localhost_only: bool
    database: str
    media_dir: str
    max_upload_bytes: int
    token_ttl_hours: int
    cors_origins: list[str]
    warnings: list[str]


class MediaOut(BaseModel):
    id: str
    original_filename: str
    sha256: str
    size_bytes: int
    extension: str
    kind: str
    container: str | None
    video_codec: str | None
    audio_codec: str | None
    width: int | None
    height: int | None
    duration_seconds: float | None
    frame_rate: float | None
    pixel_format: str | None
    rotation_degrees: int | None
    thumbnail_ready: bool
    has_proxy: bool
    validation_status: str
    validation_notes: str
    created_at: datetime
    duplicate: bool = False


class TranscodeJobOut(BaseModel):
    id: str
    media_id: str
    status: str
    error: str
    created_at: datetime
    finished_at: datetime | None


class IntegrityOut(BaseModel):
    id: str
    ok: bool
    expected_sha256: str
    actual_sha256: str | None
    detail: str


class AuditOut(BaseModel):
    id: str
    created_at: datetime
    actor: str
    action: str
    success: bool
    detail: str


class HealthCheck(BaseModel):
    status: str
    version: str
    phase: int
    time: datetime
    checks: dict[str, str]
