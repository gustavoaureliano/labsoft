"""Explicit clean showcase reset; never invoked by application startup."""

import argparse
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import NAMESPACE_URL, uuid4, uuid5

from sqlalchemy import delete, text
from sqlalchemy.orm import Session

from app.database import SessionLocal, engine
from app.integrations import get_integrations
from app.learning.models import Certificate, Lesson, LessonProgress
from app.media.inspection import inspect_video
from app.media.models import Media
from app.media.storage import BACKEND_DIR, STORAGE_ROOT
from app.showcase import LESSONS, ShowcaseIntegrations
from scripts.generate_test_video import generate_video


def upload_files(root: Path) -> list[Path]:
    """Only manage ordinary files under the two upload folders, never symlinks."""
    files = []
    for name in ("videos", "thumbnails"):
        folder = root / name
        if folder.is_symlink() or (folder.exists() and not folder.is_dir()):
            raise ValueError(f"Unsafe upload folder: {folder}")
        for path in folder.rglob("*"):
            if path.is_symlink() or not path.resolve().is_relative_to(folder):
                raise ValueError(f"Unsafe upload path: {path}")
            if path.is_file():
                files.append(path)
    return files


def reset_showcase(session: Session, root: Path, source: Path) -> dict[str, int]:
    """Replace only learning tables and files inside the explicitly supplied root."""
    if root.is_symlink():
        raise ValueError("Storage directory must not be a symlink")
    root = root.resolve()
    code_folders = [BACKEND_DIR / name for name in ("app", "scripts", "tests", "migrations")]
    code_folders.append(BACKEND_DIR.parent / "frontend")
    if root in {Path(root.anchor), BACKEND_DIR.resolve(), BACKEND_DIR.parent.resolve(), Path.home()} or any(
        root.is_relative_to(folder.resolve()) for folder in code_folders
    ):
        raise ValueError("Refusing an unsafe storage directory")
    info = inspect_video(source, "video/mp4")  # Validate before deleting anything.
    root.mkdir(parents=True, exist_ok=True)
    old_files = upload_files(root)
    new_files = []
    run_id = uuid4().hex
    now = datetime.now(timezone.utc)
    integrations = ShowcaseIntegrations()
    try:
        if session.bind.dialect.name == "postgresql":
            session.execute(text("LOCK TABLE certificates, lesson_progress, lessons, media IN ACCESS EXCLUSIVE MODE"))
        for model in (Certificate, LessonProgress, Lesson, Media):
            session.execute(delete(model))
        for course_id, lessons in LESSONS.items():
            course = integrations.course(course_id)
            key = f"videos/showcase-{course_id}-{run_id}.mp4"
            target = root / key
            target.parent.mkdir(parents=True, exist_ok=True)
            new_files.append(target)
            shutil.copyfile(source, target)
            media_id = uuid5(NAMESPACE_URL, f"aprovaai-showcase:{course_id}")
            session.add(Media(id=media_id, owner_id=course.owner_id, storage_key=key,
                              original_filename="video-demonstracao.mp4", content_type="video/mp4",
                              size_bytes=target.stat().st_size, duration_seconds=info.duration_seconds,
                              codec=info.codec, status="available"))
            session.flush()
            for position, (lesson_id, title) in enumerate(lessons, 1):
                session.add(Lesson(id=lesson_id, course_id=course_id, title=title,
                                   description=f"Aula demonstrativa de {course.title}. O vídeo de exemplo é compartilhado entre as aulas.",
                                   position=position, media_id=media_id))
                session.flush()
                complete = course_id == "redacao-nota-mil" or (course_id == "fisica-enem-mecanica" and position <= 7)
                current = course_id == "fisica-enem-mecanica" and lesson_id == "leis-newton"
                if complete or current:
                    timestamp = now if current else now - timedelta(days=1, minutes=position)
                    session.add(LessonProgress(student_id="aluno-demo", lesson_id=lesson_id,
                                               media_id=media_id, position_seconds=info.duration_seconds if complete else info.duration_seconds / 2,
                                               completed_at=timestamp if complete else None, updated_at=timestamp))
        session.commit()
    except Exception:
        session.rollback()
        for path in new_files:
            path.unlink(missing_ok=True)
        raise
    # Keep old files until the replacement data commits. Failure is reported;
    # database and disk do not have a shared transaction.
    # Recheck folders before cleanup as well, in case they changed during seeding.
    safe_files = set(upload_files(root))
    for path in old_files:
        if path in safe_files:
            path.unlink(missing_ok=True)
    return {"courses": len(LESSONS), "lessons": sum(map(len, LESSONS.values())), "media": len(LESSONS)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Replace learning data/uploads with the full showcase")
    parser.add_argument("--reset", action="store_true", help="required confirmation: deletes existing learning records/uploads")
    parser.add_argument("--database", required=True, help="database name confirmation, must match DATABASE_URL")
    args = parser.parse_args()
    if not args.reset or args.database != engine.url.database:
        parser.error("Provide --reset and the exact target database name")
    if not isinstance(get_integrations(), ShowcaseIntegrations):
        parser.error("Enable LEARNING_DEMO_MODE=true and LEARNING_DEMO_SCENARIO=showcase")
    with TemporaryDirectory(prefix="aprovaai-showcase-") as directory:
        source = Path(directory) / "demo.mp4"
        generate_video(source)
        with SessionLocal() as session:
            print(reset_showcase(session, STORAGE_ROOT, source))
