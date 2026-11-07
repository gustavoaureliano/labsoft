import pytest
from sqlalchemy import func, select

from app.integrations import get_current_user, get_integrations
from app.main import app
from app.learning.models import Certificate, Lesson
from app.media.models import Media
from app.seed_demo import reset_showcase
from app import seed_demo
from app.media.inspection import VideoInfo
from app.media.storage import BACKEND_DIR
from app.showcase import ShowcaseIntegrations
from scripts.generate_test_video import generate_video


def test_full_showcase_reset_and_browser_data(upload_context, tmp_path):
    client, sessions, root = upload_context
    source = tmp_path / "source.mp4"
    generate_video(source)
    root.mkdir()
    (root / "videos").mkdir()
    old_upload = root / "videos/old-upload.mp4"
    old_upload.write_bytes(b"old")
    unrelated = root / "notes.txt"
    unrelated.write_text("Do not remove")
    with sessions() as session:
        result = reset_showcase(session, root, source)
        assert result == {"courses": 7, "lessons": 155, "media": 7}
        assert not old_upload.exists()
        assert unrelated.read_text() == "Do not remove"
        assert session.scalar(select(func.count()).select_from(Lesson)) == 155
        assert session.scalar(select(func.count()).select_from(Certificate)) == 0
        first_keys = list(session.scalars(select(Media.storage_key)))
        reset_showcase(session, root, source)
        assert all(not (root / key).exists() for key in first_keys)
        assert len(list(root.rglob("*.mp4"))) == 7
    app.dependency_overrides[get_integrations] = ShowcaseIntegrations
    app.dependency_overrides[get_current_user] = lambda: ShowcaseIntegrations.users["aluno-demo"]
    courses = client.get("/api/learning/courses").json()
    assert len(courses) == 7 and all(item["lessons"] for item in courses)
    current = client.get("/api/learning/dashboard").json()["current_course"]
    assert current["id"] == "fisica-enem-mecanica"
    assert current["continue_lesson"]["id"] == "leis-newton"
    assert current["progress"] == 58
    mechanics = next(course for course in courses if course["id"] == "fisica-enem-mecanica")
    assert [section["title"] for section in mechanics["sections"]] == ["Cinemática", "Dinâmica e energia"]
    assert mechanics["sections"][0]["lesson_ids"] == [lesson["id"] for lesson in mechanics["lessons"][:6]]
    assert client.get("/api/learning/lessons/leis-newton/playback").json()["position_seconds"] == pytest.approx(6, abs=0.2)
    assert next(course for course in courses if course["id"] == "redacao-nota-mil")["completed"]
    app.dependency_overrides[get_current_user] = lambda: ShowcaseIntegrations.users["aluno-demo-2"]
    assert len(client.get("/api/learning/courses").json()) == 1
    assert client.get("/api/learning/lessons/q1/playback").status_code == 403


def test_bad_source_does_not_reset_existing_data(upload_context, tmp_path):
    _, sessions, root = upload_context
    source = tmp_path / "bad.mp4"
    source.write_bytes(b"not a video")
    with sessions() as session:
        session.add(Lesson(id="keep", course_id="c", title="Keep", position=1))
        session.commit()
        with pytest.raises(ValueError):
            reset_showcase(session, root, source)
        assert session.get(Lesson, "keep") is not None


def test_partial_copy_is_removed_and_old_data_is_preserved(upload_context, tmp_path, monkeypatch):
    _, sessions, root = upload_context
    source = tmp_path / "source.mp4"
    source.write_bytes(b"source")
    (root / "videos").mkdir(parents=True)
    old_upload = root / "videos/old.mp4"
    old_upload.write_bytes(b"original")
    monkeypatch.setattr(seed_demo, "inspect_video", lambda *args: VideoInfo(12, "h264"))

    def partial_copy(source, target):
        target.write_bytes(b"partial")
        raise OSError("Simulated copy failure")

    monkeypatch.setattr(seed_demo.shutil, "copyfile", partial_copy)
    with sessions() as session:
        session.add(Lesson(id="keep", course_id="c", title="Keep", position=1))
        session.commit()
        with pytest.raises(OSError, match="Simulated copy failure"):
            reset_showcase(session, root, source)
        assert session.get(Lesson, "keep") is not None
        assert list((root / "videos").iterdir()) == [old_upload]
        assert old_upload.read_bytes() == b"original"


@pytest.mark.parametrize("link_kind", ["root", "videos", "nested-directory", "file"])
def test_symlinks_are_rejected_without_deleting_files(upload_context, tmp_path, monkeypatch, link_kind):
    _, sessions, root = upload_context
    outside = tmp_path / "outside"
    outside.mkdir()
    protected = outside / "keep.mp4"
    protected.write_bytes(b"protected")
    source = tmp_path / "source.mp4"
    source.write_bytes(b"source")
    monkeypatch.setattr(seed_demo, "inspect_video", lambda *args: VideoInfo(12, "h264"))
    if link_kind == "root":
        root.symlink_to(outside, target_is_directory=True)
    else:
        root.mkdir()
        if link_kind == "videos":
            (root / "videos").symlink_to(outside, target_is_directory=True)
        else:
            (root / "videos").mkdir()
            if link_kind == "file":
                (root / "videos/link.mp4").symlink_to(protected)
            else:
                (root / "videos/nested").symlink_to(outside, target_is_directory=True)
    with sessions() as session:
        session.add(Lesson(id="keep", course_id="c", title="Keep", position=1))
        session.commit()
        with pytest.raises(ValueError):
            reset_showcase(session, root, source)
        assert session.get(Lesson, "keep") is not None
        assert protected.read_bytes() == b"protected"


def test_source_code_directory_is_not_a_reset_target(upload_context, tmp_path):
    _, sessions, _ = upload_context
    with sessions() as session:
        with pytest.raises(ValueError, match="unsafe storage directory"):
            reset_showcase(session, BACKEND_DIR / "app", tmp_path / "unused.mp4")
