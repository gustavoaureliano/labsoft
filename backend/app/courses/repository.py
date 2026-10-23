"""Persistence operations for courses."""

from uuid import UUID

from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session

from app.media.models import Media

from .models import Course, CourseLesson, CourseMaterial, CourseReview, Enrollment


class CourseRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, course_id: UUID, *, published_only: bool = False) -> Course | None:
        query = select(Course).where(Course.id == course_id)
        if published_only:
            query = query.where(Course.status == "published")
        return self.session.scalar(query)

    def add(self, course: Course) -> Course:
        self.session.add(course)
        return course

    def list_published(
        self,
        *,
        subject: str | None = None,
        area: str | None = None,
        access_type: str | None = None,
        term: str | None = None,
        order: str = "relevance",
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Course], int]:
        filters = [Course.status == "published"]
        if subject:
            filters.append(func.lower(Course.subject) == subject.lower())
        if area:
            filters.append(func.lower(Course.area) == area.lower())
        if access_type:
            filters.append(Course.access_type == access_type)
        if term:
            filters.append(Course.search_text.contains(term))

        total = self.session.scalar(
            select(func.count()).select_from(Course).where(*filters)
        ) or 0
        query = select(Course).where(*filters)
        if order == "title":
            query = query.order_by(Course.title.asc())
        elif order == "newest":
            query = query.order_by(Course.published_at.desc(), Course.created_at.desc())
        elif order == "popular":
            query = query.order_by(Course.view_count.desc(), Course.published_at.desc())
        else:
            query = query.order_by(Course.featured.desc(), Course.view_count.desc())
        return list(self.session.scalars(query.offset(offset).limit(limit))), total

    def list_by_teacher(self, teacher_id: UUID) -> list[Course]:
        query = (
            select(Course)
            .where(Course.teacher_id == teacher_id)
            .order_by(Course.updated_at.desc())
        )
        return list(self.session.scalars(query))

    def list_lessons(self, course_id: UUID) -> list[CourseLesson]:
        query = (
            select(CourseLesson)
            .where(CourseLesson.course_id == course_id)
            .order_by(CourseLesson.position, CourseLesson.created_at)
        )
        return list(self.session.scalars(query))

    def get_lesson(self, course_id: UUID, lesson_id: UUID) -> CourseLesson | None:
        return self.session.scalar(
            select(CourseLesson).where(
                CourseLesson.id == lesson_id, CourseLesson.course_id == course_id
            )
        )

    def add_lesson(self, lesson: CourseLesson) -> CourseLesson:
        self.session.add(lesson)
        return lesson

    def delete_lesson(self, lesson: CourseLesson) -> None:
        self.session.delete(lesson)

    def list_materials(
        self, course_id: UUID, lesson_id: UUID | None = None
    ) -> list[CourseMaterial]:
        query = select(CourseMaterial).where(CourseMaterial.course_id == course_id)
        if lesson_id:
            query = query.where(CourseMaterial.lesson_id == lesson_id)
        return list(self.session.scalars(query.order_by(CourseMaterial.position)))

    def get_material(self, course_id: UUID, material_id: UUID) -> CourseMaterial | None:
        return self.session.scalar(
            select(CourseMaterial).where(
                CourseMaterial.id == material_id,
                CourseMaterial.course_id == course_id,
            )
        )

    def add_material(self, material: CourseMaterial) -> CourseMaterial:
        self.session.add(material)
        return material

    def delete_material(self, material: CourseMaterial) -> None:
        self.session.delete(material)

    def search_materials(self, term: str, limit: int = 20) -> list[CourseMaterial]:
        query = (
            select(CourseMaterial)
            .join(Course, Course.id == CourseMaterial.course_id)
            .where(
                Course.status == "published",
                or_(
                    func.lower(CourseMaterial.title).contains(term),
                    func.lower(CourseMaterial.description).contains(term),
                    func.lower(CourseMaterial.kind).contains(term),
                ),
            )
            .order_by(CourseMaterial.title)
            .limit(limit)
        )
        return list(self.session.scalars(query))

    def get_media(self, media_id: UUID) -> Media | None:
        return self.session.get(Media, media_id)

    def add_media(self, media: Media) -> Media:
        self.session.add(media)
        return media

    def delete_media(self, media: Media) -> None:
        self.session.delete(media)

    def has_access(self, student_id: UUID, course_id: UUID) -> bool:
        enrollment = self.session.scalar(
            select(Enrollment.id).where(
                Enrollment.student_id == student_id,
                Enrollment.course_id == course_id,
                Enrollment.status.in_(("active", "completed")),
            )
        )
        return enrollment is not None

    def enrolled_course_ids(self, student_id: UUID) -> set[UUID]:
        query = select(Enrollment.course_id).where(
            Enrollment.student_id == student_id,
            Enrollment.status.in_(("active", "completed")),
        )
        return set(self.session.scalars(query))

    def enrollment_count(self, course_id: UUID) -> int:
        return self.session.scalar(
            select(func.count()).select_from(Enrollment).where(
                Enrollment.course_id == course_id,
                Enrollment.status.in_(("active", "completed")),
            )
        ) or 0

    def lesson_count(self, course_id: UUID) -> int:
        return self.session.scalar(
            select(func.count()).select_from(CourseLesson).where(
                CourseLesson.course_id == course_id
            )
        ) or 0

    def material_count(self, course_id: UUID) -> int:
        return self.session.scalar(
            select(func.count()).select_from(CourseMaterial).where(
                CourseMaterial.course_id == course_id
            )
        ) or 0

    def rating(self, course_id: UUID) -> float | None:
        value = self.session.scalar(
            select(func.avg(CourseReview.rating)).where(CourseReview.course_id == course_id)
        )
        return round(float(value), 2) if value is not None else None

    def reviews(self, course_id: UUID, limit: int = 20) -> list[CourseReview]:
        query = (
            select(CourseReview)
            .where(CourseReview.course_id == course_id)
            .order_by(CourseReview.created_at.desc())
            .limit(limit)
        )
        return list(self.session.scalars(query))

    def delete_course_data(self, course_id: UUID) -> None:
        self.session.execute(delete(CourseReview).where(CourseReview.course_id == course_id))
