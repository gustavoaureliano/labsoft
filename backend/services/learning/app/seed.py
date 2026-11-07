"""Explicit development lessons: python -m app.seed. Never runs on startup."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.integrations import get_integrations
from app.learning.models import Lesson
from app.media.models import Media

FIXTURES = (
    ("demo-quantica-introducao", "fisica-quantica", "Introdução", 1),
    ("demo-quantica-radiacao", "fisica-quantica", "Radiação de corpo negro", 2),
    ("demo-mecanica-vetores", "fisica-enem-mecanica", "Grandezas e vetores", 1),
    ("demo-mecanica-movimento", "fisica-enem-mecanica", "Movimento uniforme", 2),
)


def seed_lessons(session: Session) -> int:
    created = 0
    for lesson_id, course_id, title, position in FIXTURES:
        occupied = session.scalar(select(Lesson).where(
            Lesson.course_id == course_id, Lesson.position == position
        ))
        if session.get(Lesson, lesson_id) is not None or occupied is not None:
            continue
        session.add(Lesson(id=lesson_id, course_id=course_id, title=title, position=position))
        session.flush()
        created += 1
    session.commit()
    return created


if __name__ == "__main__":
    get_integrations()  # Refuse to seed without explicit development mode.
    with SessionLocal() as session:
        print(f"Aulas criadas: {seed_lessons(session)}; registros existentes preservados.")
