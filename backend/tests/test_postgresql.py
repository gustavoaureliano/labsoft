"""Opt-in real PostgreSQL checks, isolated in schemas in a dedicated test DB."""

import os
import subprocess
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session


@pytest.fixture
def postgres_engine():
    raw = os.environ.get("TEST_DATABASE_URL")
    if not raw:
        pytest.skip("Set TEST_DATABASE_URL to a dedicated database ending in _test")
    url = make_url(raw)
    if not (url.database or "").endswith("_test") or url.get_backend_name() != "postgresql":
        pytest.fail("Refusing PostgreSQL tests outside a database ending in _test")
    admin = create_engine(url)
    schema = f"learning_test_{uuid4().hex}"
    with admin.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA "{schema}"'))
    scoped = url.update_query_dict({"options": f"-csearch_path={schema}"})
    engine = create_engine(scoped)
    try:
        environment = {**os.environ, "DATABASE_URL": scoped.render_as_string(hide_password=False)}
        subprocess.run([".venv/bin/alembic", "upgrade", "head"], env=environment, check=True, capture_output=True)
        yield engine
    finally:
        engine.dispose()
        with admin.begin() as conn:
            conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin.dispose()


def test_migrations_and_metadata_match(postgres_engine):
    env = {**os.environ, "DATABASE_URL": postgres_engine.url.render_as_string(hide_password=False)}
    subprocess.run([".venv/bin/alembic", "check"], env=env, check=True, capture_output=True)
    # Exercise the new revision from the previous schema without touching app data.
    subprocess.run([".venv/bin/alembic", "downgrade", "-1"], env=env, check=True, capture_output=True)
    subprocess.run([".venv/bin/alembic", "upgrade", "head"], env=env, check=True, capture_output=True)


def test_real_postgres_foreign_key(postgres_engine):
    from sqlalchemy.exc import IntegrityError
    from app.learning.models import Lesson
    with Session(postgres_engine) as session:
        session.add(Lesson(course_id="test", title="Missing media", position=1, media_id=uuid4()))
        with pytest.raises(IntegrityError):
            session.flush()
        session.rollback()


def test_concurrent_course_reordering(postgres_engine):
    from concurrent.futures import ThreadPoolExecutor
    from app.learning.models import Lesson
    from app.learning.service import reorder_lessons
    with Session(postgres_engine) as session:
        session.add_all([Lesson(id="a", course_id="c", title="A", position=1), Lesson(id="b", course_id="c", title="B", position=2)])
        session.commit()
    def reorder(ids):
        with Session(postgres_engine) as session:
            reorder_lessons(session, "c", ids)
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(reorder, [["b", "a"], ["a", "b"]]))
    with Session(postgres_engine) as session:
        assert sorted(session.query(Lesson.position).all()) == [(1,), (2,)]


def test_concurrent_first_progress_and_delete_cascade(postgres_engine):
    from concurrent.futures import ThreadPoolExecutor
    from app.learning.models import Lesson, LessonProgress
    from app.media.models import Media
    from app.learning.progress import save_progress
    with Session(postgres_engine) as session:
        media = Media(storage_key="videos/test.mp4", original_filename="test.mp4", content_type="video/mp4", size_bytes=1, status="available", duration_seconds=12)
        session.add(media)
        session.flush()
        media_id = media.id
        session.add(Lesson(id="lesson", course_id="course", title="A", position=1, media_id=media_id))
        session.commit()
    def save(position):
        with Session(postgres_engine) as session:
            save_progress(session, "student", "lesson", media_id, position)
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(save, [3, 4]))
    with Session(postgres_engine) as session:
        assert session.query(LessonProgress).count() == 1
        assert session.get(LessonProgress, ("student", "lesson")).position_seconds in (3, 4)
        session.delete(session.get(Lesson, "lesson"))
        session.commit()
        assert session.query(LessonProgress).count() == 0
