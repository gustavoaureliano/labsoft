"""Prepare only the dedicated test database and test storage, never app data."""

import os
import subprocess
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from PIL import Image

from app.learning.models import Lesson
from app.media.models import Media
from app.seed import seed_lessons
from scripts.generate_test_video import generate_video


if __name__ == "__main__":
    url = make_url(os.environ["TEST_DATABASE_URL"])
    if not (url.database or "").endswith("_test"):
        raise RuntimeError("Dedicated _test database required")
    root = Path(os.environ["STORAGE_DIR"]).resolve()
    if "opencode" not in str(root) and "test" not in root.name:
        raise RuntimeError("Explicit test storage directory required")
    path = root / "videos/e2e-fixture.mp4"
    if not path.exists():
        generate_video(path)
    image_path = root / "thumbnails/e2e-fixture.png"
    image_path.parent.mkdir(parents=True, exist_ok=True)
    if not image_path.exists():
        Image.new("RGB", (320, 180), "#075a76").save(image_path)
    subprocess.run([".venv/bin/alembic", "upgrade", "head"], env={**os.environ, "DATABASE_URL": url.render_as_string(hide_password=False)}, check=True)
    engine = create_engine(url)
    with Session(engine) as session:
        seed_lessons(session)
        media_id = uuid5(NAMESPACE_URL, "aprovaai-e2e-fixture")
        media = session.get(Media, media_id)
        if media is None:
            media = Media(id=media_id, storage_key="videos/e2e-fixture.mp4", original_filename="e2e-fixture.mp4", content_type="video/mp4", size_bytes=path.stat().st_size, status="available", owner_id="professor-demo", duration_seconds=12, codec="h264")
            session.add(media)
            session.flush()
        for lesson_id in ("demo-quantica-introducao", "demo-quantica-radiacao", "demo-mecanica-vetores", "demo-mecanica-movimento"):
            lesson = session.get(Lesson, lesson_id)
            if lesson:
                lesson.media_id = media_id
        session.commit()
    engine.dispose()
    print("Dedicated test lessons/video ready")
