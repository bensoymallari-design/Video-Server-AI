from __future__ import annotations

import subprocess
import time
from pathlib import Path

from tests.helpers import login


def _video(path: Path) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "testsrc=size=320x180:rate=24",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:sample_rate=48000",
            "-t",
            "1",
            "-pix_fmt",
            "yuv420p",
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            str(path),
        ],
        check=True,
    )


def _png(path: Path) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "color=c=red:s=64x64",
            "-frames:v",
            "1",
            str(path),
        ],
        check=True,
    )


def test_upload_inspects_video_and_image_without_replacing_the_original(client, tmp_path: Path) -> None:
    login(client)
    video = tmp_path / "wall.mp4"
    image = tmp_path / "logo.png"
    _video(video)
    _png(image)
    original_bytes = video.read_bytes()

    with video.open("rb") as handle:
        uploaded = client.post("/media", files={"file": ("wall.mp4", handle, "video/mp4")})
    assert uploaded.status_code == 200, uploaded.text
    body = uploaded.json()
    assert body["duplicate"] is False
    assert body["kind"] == "video"
    assert body["width"] == 320
    assert body["height"] == 180
    assert body["video_codec"] == "h264"
    assert body["audio_codec"] == "aac"
    assert body["frame_rate"] == 24
    assert 0.9 <= body["duration_seconds"] <= 1.2
    assert body["thumbnail_ready"] is True
    assert body["validation_notes"].startswith("Original file was stored without re-encoding")

    thumb = client.get(f"/media/{body['id']}/thumbnail")
    assert thumb.status_code == 200
    assert thumb.headers["content-type"].startswith("image/jpeg")
    assert thumb.content[:3] == b"\xff\xd8\xff"

    probe = client.get(f"/media/{body['id']}/probe")
    assert probe.status_code == 200
    assert probe.json()["streams"]

    verified = client.get(f"/media/{body['id']}/verify").json()
    assert verified["ok"] is True
    assert verified["actual_sha256"] == body["sha256"]

    with video.open("rb") as handle:
        duplicate = client.post("/media", files={"file": ("copy.mp4", handle, "video/mp4")})
    assert duplicate.status_code == 200
    assert duplicate.json()["duplicate"] is True
    assert duplicate.json()["id"] == body["id"]
    assert len(client.get("/media").json()) == 1

    with image.open("rb") as handle:
        picture = client.post("/media", files={"file": ("logo.png", handle, "image/png")})
    assert picture.status_code == 200, picture.text
    assert picture.json()["kind"] == "image"
    assert picture.json()["width"] == 64
    assert picture.json()["height"] == 64

    listed = {item["original_filename"] for item in client.get("/media").json()}
    assert listed == {"logo.png", "wall.mp4"}
    assert original_bytes == video.read_bytes()


def test_invalid_and_disallowed_uploads_are_rejected(client) -> None:
    login(client)
    before = {item["id"] for item in client.get("/media").json()}
    rejected = client.post("/media", files={"file": ("notes.txt", b"hello", "text/plain")})
    assert rejected.status_code == 415
    invalid = client.post("/media", files={"file": ("broken.mp4", b"not-a-media-file", "video/mp4")})
    assert invalid.status_code == 422
    empty = client.post("/media", files={"file": ("empty.png", b"", "image/png")})
    assert empty.status_code == 400
    after = {item["id"] for item in client.get("/media").json()}
    assert after == before


def test_upload_limit(client, monkeypatch) -> None:
    login(client)
    from app.config import get_settings

    before = {item["id"] for item in client.get("/media").json()}
    monkeypatch.setattr(get_settings(), "max_upload_bytes", 32)
    rejected = client.post("/media", files={"file": ("big.png", b"x" * 64, "image/png")})
    assert rejected.status_code == 413
    after = {item["id"] for item in client.get("/media").json()}
    assert after == before


def test_transcode_creates_a_proxy_and_delete_removes_the_asset(client, tmp_path: Path) -> None:
    login(client)
    video = tmp_path / "spot.mp4"
    _video(video)
    with video.open("rb") as handle:
        uploaded = client.post("/media", files={"file": ("spot.mp4", handle, "video/mp4")})
    media_id = uploaded.json()["id"]
    picture = tmp_path / "still.png"
    _png(picture)
    with picture.open("rb") as handle:
        image = client.post("/media", files={"file": ("still.png", handle, "image/png")})
    assert client.post(f"/media/{image.json()['id']}/transcode").status_code == 400

    started = client.post(f"/media/{media_id}/transcode")
    assert started.status_code == 202, started.text
    job_id = started.json()["id"]
    status = started.json()["status"]
    for _ in range(100):
        if status in {"succeeded", "failed"}:
            break
        time.sleep(0.2)
        status = client.get(f"/media/jobs/{job_id}").json()["status"]
    job = client.get(f"/media/jobs/{job_id}").json()
    assert job["status"] == "succeeded", job
    assert client.get(f"/media/{media_id}").json()["has_proxy"] is True

    assert client.delete(f"/media/{media_id}").status_code == 204
    assert client.get(f"/media/{media_id}").status_code == 404
    assert client.delete(f"/media/{image.json()['id']}").status_code == 204
