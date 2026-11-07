import subprocess

import pytest

from app.media import inspection, service
from app.media.inspection import InvalidVideo, InspectionUnavailable, inspect_video
from scripts.generate_test_video import generate_video


@pytest.mark.parametrize("extension,mime", [(".mp4", "video/mp4"), (".webm", "video/webm")])
def test_real_upload_and_inspection(upload_context, tmp_path, monkeypatch, extension, mime):
    client, _, _ = upload_context
    monkeypatch.setattr(service, "inspect_video", inspect_video)
    path = tmp_path / f"fixture{extension}"
    generate_video(path)
    with path.open("rb") as file:
        response = client.post("/api/media", files={"file": (path.name, file, mime)})
    assert response.status_code == 201, response.text
    assert response.json()["duration_seconds"] == pytest.approx(12, abs=0.2)


def test_invalid_video_cleans_file(upload_context, monkeypatch):
    client, sessions, root = upload_context
    monkeypatch.setattr(service, "inspect_video", inspect_video)
    response = client.post("/api/media", files={"file": ("fake.mp4", b"not a video", "video/mp4")})
    assert response.status_code == 400
    assert list(root.rglob("*.mp4")) == []


@pytest.mark.parametrize("error,expected", [(FileNotFoundError(), InspectionUnavailable), (subprocess.TimeoutExpired("ffprobe", 15), InvalidVideo)])
def test_probe_failure(monkeypatch, tmp_path, error, expected):
    def fail(*args, **kwargs):
        raise error
    monkeypatch.setattr(inspection.subprocess, "run", fail)
    with pytest.raises(expected):
        inspect_video(tmp_path / "a.mp4", "video/mp4")
