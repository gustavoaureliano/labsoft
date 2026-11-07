"""Explicit legacy ownership assignment; does not alter media contents."""

import argparse
from uuid import UUID

from sqlalchemy import select

from app.database import SessionLocal
from app.integrations import get_integrations
from app.learning.models import Lesson
from app.media.models import Media


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("media_id", type=UUID)
    parser.add_argument("owner_id")
    args = parser.parse_args()
    integrations = get_integrations()
    owner = integrations.user(args.owner_id)
    if owner is None or owner.role != "teacher":
        parser.error("O proprietário precisa ser um professor conhecido")
    with SessionLocal() as session:
        media = session.get(Media, args.media_id)
        if media is None or media.owner_id is not None:
            parser.error("Mídia inexistente ou já possui proprietário")
        for course_id in session.scalars(select(Lesson.course_id).where(Lesson.media_id == media.id)):
            course = integrations.course(course_id)
            if course is None or course.owner_id != owner.id:
                parser.error("Professor não é proprietário de todos os cursos associados")
        media.owner_id = owner.id
        session.commit()
        print("Proprietário atribuído; arquivo e associações preservados.")
