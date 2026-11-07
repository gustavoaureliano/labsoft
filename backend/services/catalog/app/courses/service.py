"""Business rules for catalog, course management, and publication."""

import math
import unicodedata
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.media.models import Media

from .exceptions import (
    CourseForbidden,
    CourseNotFound,
    CourseValidationError,
    LessonNotFound,
    MaterialNotFound,
    MediaNotFound,
)
from .models import Course, CourseLesson, CourseMaterial
from .repository import CourseRepository
from .schemas import (
    AccessResponse,
    CourseCreate,
    CourseDetailsResponse,
    CoursePage,
    CoursePreviewResponse,
    CourseResponse,
    CourseSummary,
    CourseUpdate,
    LandingResponse,
    LessonCreate,
    LessonResponse,
    LessonUpdate,
    MaterialCreate,
    MaterialListResponse,
    MaterialResponse,
    MaterialUpdate,
    Pagination,
    PublicationResponse,
    RecommendationResponse,
    SearchResponse,
    TeacherCourseSummary,
    TeacherDashboardResponse,
)


def normalize_text(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    return " ".join(
        "".join(char for char in decomposed if not unicodedata.combining(char))
        .lower()
        .split()
    )


def course_search_text(course: Course) -> str:
    return normalize_text(
        " ".join(
            [
                course.title,
                course.subject,
                course.area,
                course.summary,
                course.teacher_name,
                *course.exams,
            ]
        )
    )


class BaseCourseService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = CourseRepository(session)

    def _course(self, course_id: UUID, *, published_only: bool = False) -> Course:
        course = self.repository.get(course_id, published_only=published_only)
        if not course:
            raise CourseNotFound("Curso não encontrado.")
        return course

    def _owned_course(self, course_id: UUID, teacher_id: UUID) -> Course:
        course = self._course(course_id)
        if course.teacher_id != teacher_id:
            raise CourseForbidden("O curso pertence a outro professor.")
        return course

    def _summary(self, course: Course) -> CourseSummary:
        data = CourseResponse.model_validate(course).model_dump()
        return CourseSummary(
            **data,
            lesson_count=self.repository.lesson_count(course.id),
            student_count=self.repository.enrollment_count(course.id),
            rating=self.repository.rating(course.id),
        )


class CourseService(BaseCourseService):
    def _validate_access(self, access_type: str, price: Decimal | None) -> Decimal | None:
        if access_type == "free":
            return Decimal("0.00")
        if price is None or price <= 0:
            raise CourseValidationError("Curso pago exige preço maior que zero.")
        return price

    def create(
        self, payload: CourseCreate, *, teacher_id: UUID, teacher_name: str
    ) -> CourseResponse:
        data = payload.model_dump()
        data["access_type"] = payload.access_type.value
        data["price"] = self._validate_access(data["access_type"], data["price"])
        data["exams"] = sorted({item.strip() for item in data["exams"] if item.strip()})
        course = Course(
            **data,
            teacher_id=teacher_id,
            teacher_name=teacher_name.strip() or "Professor",
            status="draft",
        )
        course.search_text = course_search_text(course)
        self.repository.add(course)
        self.session.commit()
        self.session.refresh(course)
        return CourseResponse.model_validate(course)

    def update(
        self, course_id: UUID, payload: CourseUpdate, *, teacher_id: UUID
    ) -> CourseResponse:
        course = self._owned_course(course_id, teacher_id)
        changes = payload.model_dump(exclude_unset=True)
        if "access_type" in changes:
            changes["access_type"] = payload.access_type.value if payload.access_type else None
        access_type = changes.get("access_type", course.access_type)
        price = changes.get("price", course.price)
        changes["price"] = self._validate_access(access_type, price)
        if changes.get("exams") is not None:
            changes["exams"] = sorted(
                {item.strip() for item in changes["exams"] if item.strip()}
            )
        for field, value in changes.items():
            setattr(course, field, value)
        course.search_text = course_search_text(course)
        self.session.commit()
        self.session.refresh(course)
        return CourseResponse.model_validate(course)

    def add_lesson(
        self, course_id: UUID, payload: LessonCreate, *, teacher_id: UUID
    ) -> LessonResponse:
        self._owned_course(course_id, teacher_id)
        lesson = CourseLesson(course_id=course_id, **payload.model_dump())
        self.repository.add_lesson(lesson)
        self.session.commit()
        self.session.refresh(lesson)
        return LessonResponse.model_validate(lesson)

    def update_lesson(
        self,
        course_id: UUID,
        lesson_id: UUID,
        payload: LessonUpdate,
        *,
        teacher_id: UUID,
    ) -> LessonResponse:
        self._owned_course(course_id, teacher_id)
        lesson = self.repository.get_lesson(course_id, lesson_id)
        if not lesson:
            raise LessonNotFound("Aula não encontrada.")
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(lesson, field, value)
        self.session.commit()
        self.session.refresh(lesson)
        return LessonResponse.model_validate(lesson)

    def delete_lesson(self, course_id: UUID, lesson_id: UUID, *, teacher_id: UUID) -> None:
        self._owned_course(course_id, teacher_id)
        lesson = self.repository.get_lesson(course_id, lesson_id)
        if not lesson:
            raise LessonNotFound("Aula não encontrada.")
        self.repository.delete_lesson(lesson)
        self.session.commit()


class CatalogService(BaseCourseService):
    def list_courses(
        self,
        *,
        subject: str | None,
        area: str | None,
        exam: str | None,
        access_type: str | None,
        order: str,
        page: int,
        size: int,
        term: str | None = None,
    ) -> CoursePage:
        normalized_term = normalize_text(term) if term else None
        if exam or order == "rating":
            candidates, _ = self.repository.list_published(
                subject=subject,
                area=area,
                access_type=access_type,
                term=normalized_term,
                order=order,
                offset=0,
                limit=1000,
            )
            if exam:
                candidates = [
                    course
                    for course in candidates
                    if normalize_text(exam)
                    in {normalize_text(item) for item in course.exams}
                ]
            if order == "rating":
                candidates.sort(
                    key=lambda course: self.repository.rating(course.id) or 0,
                    reverse=True,
                )
            total = len(candidates)
            courses = candidates[(page - 1) * size : page * size]
        else:
            courses, total = self.repository.list_published(
                subject=subject,
                area=area,
                access_type=access_type,
                term=normalized_term,
                order=order,
                offset=(page - 1) * size,
                limit=size,
            )
        return CoursePage(
            items=[self._summary(course) for course in courses],
            pagination=Pagination(
                page=page,
                size=size,
                total=total,
                pages=math.ceil(total / size) if total else 0,
            ),
        )

    def landing(self) -> LandingResponse:
        sample, _ = self.repository.list_published(order="newest", limit=6)
        featured = [course for course in sample if course.featured]
        if len(featured) < 3:
            popular, _ = self.repository.list_published(order="popular", limit=6)
            known = {course.id for course in featured}
            featured.extend(course for course in popular if course.id not in known)
        return LandingResponse(
            sample_courses=[self._summary(course) for course in sample],
            featured_courses=[self._summary(course) for course in featured[:6]],
            access_options=["free", "single_purchase", "subscription"],
        )

    def search(self, term: str, *, limit: int = 20) -> SearchResponse:
        normalized = normalize_text(term)
        courses, _ = self.repository.list_published(term=normalized, limit=limit)
        materials = self.repository.search_materials(term.lower(), limit=limit)
        material_items = [
            MaterialResponse.model_validate(material).model_copy(
                update={"authorized": material.access_level == "public"}
            )
            for material in materials
        ]
        return SearchResponse(
            courses=[self._summary(course) for course in courses],
            materials=material_items,
            total=len(courses) + len(material_items),
        )

    def details(
        self, course_id: UUID, *, student_id: UUID | None
    ) -> CourseDetailsResponse:
        course = self._course(course_id, published_only=True)
        course.view_count += 1
        self.session.commit()
        access = AccessService(self.session).check(course, student_id=student_id)
        lessons = self.repository.list_lessons(course.id)
        reviews = self.repository.reviews(course.id)
        return CourseDetailsResponse(
            course=self._summary(course),
            access=access,
            lessons=[LessonResponse.model_validate(item) for item in lessons],
            reviews=[
                {
                    "rating": item.rating,
                    "comment": item.comment,
                    "created_at": item.created_at.isoformat(),
                }
                for item in reviews
            ],
        )


class AccessService(BaseCourseService):
    def check(self, course: Course, *, student_id: UUID | None) -> AccessResponse:
        if course.access_type == "free":
            return AccessResponse(allowed=True, reason="free_course", acquisition_required=False)
        if student_id and self.repository.has_access(student_id, course.id):
            return AccessResponse(allowed=True, reason="enrolled", acquisition_required=False)
        return AccessResponse(allowed=False, reason="purchase_required", acquisition_required=True)


class RecommendationService(BaseCourseService):
    def recommend(self, student_id: UUID, *, limit: int = 6) -> RecommendationResponse:
        enrolled_ids = self.repository.enrolled_course_ids(student_id)
        all_courses, _ = self.repository.list_published(order="popular", limit=1000)
        enrolled_courses = [course for course in all_courses if course.id in enrolled_ids]
        available = [course for course in all_courses if course.id not in enrolled_ids]
        subjects = {normalize_text(course.subject) for course in enrolled_courses}
        exams = {normalize_text(exam) for course in enrolled_courses for exam in course.exams}

        def score(course: Course) -> tuple[float, int]:
            rating = self.repository.rating(course.id) or 0
            subject_score = 4 if normalize_text(course.subject) in subjects else 0
            exam_score = 3 * len(exams & {normalize_text(exam) for exam in course.exams})
            popularity = min(self.repository.enrollment_count(course.id), 100) / 20
            return subject_score + exam_score + rating + popularity, course.view_count

        available.sort(key=score, reverse=True)
        return RecommendationResponse(
            items=[self._summary(course) for course in available[:limit]],
            strategy="history_subject_exam_popularity" if enrolled_courses else "popularity_rating",
        )


class TeacherCourseService(BaseCourseService):
    def dashboard(self, teacher_id: UUID) -> TeacherDashboardResponse:
        courses = self.repository.list_by_teacher(teacher_id)
        items = []
        for course in courses:
            summary = self._summary(course).model_dump()
            items.append(
                TeacherCourseSummary(
                    **summary, material_count=self.repository.material_count(course.id)
                )
            )
        return TeacherDashboardResponse(
            items=items,
            total_courses=len(items),
            published_courses=sum(item.status == "published" for item in items),
            draft_courses=sum(item.status == "draft" for item in items),
            total_students=sum(item.student_count for item in items),
        )


class MaterialService(BaseCourseService):
    def create(
        self, course_id: UUID, payload: MaterialCreate, *, teacher_id: UUID
    ) -> MaterialResponse:
        self._owned_course(course_id, teacher_id)
        if bool(payload.media_id) == bool(payload.external_url):
            raise CourseValidationError(
                "Informe exatamente uma origem: media_id ou external_url."
            )
        if payload.lesson_id and not self.repository.get_lesson(course_id, payload.lesson_id):
            raise LessonNotFound("Aula não encontrada neste curso.")
        if payload.media_id:
            media = self.repository.get_media(payload.media_id)
            if not media or media.status != "available":
                raise MediaNotFound("Mídia não encontrada ou indisponível.")
        data = payload.model_dump()
        data["access_level"] = payload.access_level.value
        data["external_url"] = str(payload.external_url) if payload.external_url else None
        material = CourseMaterial(course_id=course_id, **data)
        self.repository.add_material(material)
        self.session.commit()
        self.session.refresh(material)
        return MaterialResponse.model_validate(material)

    def create_from_upload(
        self,
        course_id: UUID,
        *,
        media: Media,
        title: str,
        description: str,
        kind: str,
        access_level: str,
        position: int,
        lesson_id: UUID | None,
        teacher_id: UUID,
    ) -> MaterialResponse:
        self._owned_course(course_id, teacher_id)
        if lesson_id and not self.repository.get_lesson(course_id, lesson_id):
            raise LessonNotFound("Aula não encontrada neste curso.")
        self.repository.add_media(media)
        self.session.flush()
        material = CourseMaterial(
            course_id=course_id,
            media_id=media.id,
            lesson_id=lesson_id,
            title=title,
            description=description,
            kind=kind,
            access_level=access_level,
            position=position,
        )
        self.repository.add_material(material)
        self.session.commit()
        self.session.refresh(material)
        return MaterialResponse.model_validate(material)

    def update(
        self,
        course_id: UUID,
        material_id: UUID,
        payload: MaterialUpdate,
        *,
        teacher_id: UUID,
    ) -> MaterialResponse:
        self._owned_course(course_id, teacher_id)
        material = self.repository.get_material(course_id, material_id)
        if not material:
            raise MaterialNotFound("Material não encontrado.")
        changes = payload.model_dump(exclude_unset=True)
        if "access_level" in changes and payload.access_level:
            changes["access_level"] = payload.access_level.value
        if "external_url" in changes and payload.external_url:
            changes["external_url"] = str(payload.external_url)
        if changes.get("lesson_id") and not self.repository.get_lesson(
            course_id, changes["lesson_id"]
        ):
            raise LessonNotFound("Aula não encontrada neste curso.")
        for field, value in changes.items():
            setattr(material, field, value)
        self.session.commit()
        self.session.refresh(material)
        return MaterialResponse.model_validate(material)

    def delete(
        self, course_id: UUID, material_id: UUID, *, teacher_id: UUID
    ) -> Media | None:
        self._owned_course(course_id, teacher_id)
        material = self.repository.get_material(course_id, material_id)
        if not material:
            raise MaterialNotFound("Material não encontrado.")
        media = self.repository.get_media(material.media_id) if material.media_id else None
        self.repository.delete_material(material)
        if media:
            self.repository.delete_media(media)
        self.session.commit()
        return media

    def list_authorized(
        self,
        course_id: UUID,
        *,
        student_id: UUID | None,
        lesson_id: UUID | None,
        download_url_factory,
    ) -> MaterialListResponse:
        course = self._course(course_id, published_only=True)
        access = AccessService(self.session).check(course, student_id=student_id)
        items = []
        for material in self.repository.list_materials(course_id, lesson_id):
            authorized = material.access_level == "public" or access.allowed
            download_url = None
            if authorized:
                if material.external_url:
                    download_url = material.external_url
                elif material.media_id:
                    download_url = download_url_factory(material.media_id)
            items.append(
                MaterialResponse.model_validate(material).model_copy(
                    update={"authorized": authorized, "download_url": download_url}
                )
            )
        return MaterialListResponse(course_id=course_id, access=access, items=items)


class PublishingService(BaseCourseService):
    def pending(self, course: Course) -> list[str]:
        pending = []
        if not course.title.strip():
            pending.append("title")
        if not course.subject.strip():
            pending.append("subject")
        if not course.summary.strip():
            pending.append("summary")
        if course.access_type == "paid" and (course.price is None or course.price <= 0):
            pending.append("price")
        lessons = self.repository.list_lessons(course.id)
        if not lessons:
            pending.append("lessons")
        for material in self.repository.list_materials(course.id):
            if material.media_id:
                media = self.repository.get_media(material.media_id)
                if not media or media.status != "available":
                    pending.append(f"material:{material.id}")
        return pending

    def preview(self, course_id: UUID, *, teacher_id: UUID) -> CoursePreviewResponse:
        course = self._owned_course(course_id, teacher_id)
        return CoursePreviewResponse(
            course=CourseResponse.model_validate(course),
            lessons=[
                LessonResponse.model_validate(item)
                for item in self.repository.list_lessons(course_id)
            ],
            materials=[
                MaterialResponse.model_validate(item)
                for item in self.repository.list_materials(course_id)
            ],
            publication_pending=self.pending(course),
        )

    def set_publication(
        self, course_id: UUID, *, action: str, teacher_id: UUID
    ) -> PublicationResponse:
        course = self._owned_course(course_id, teacher_id)
        if action == "publish":
            pending = self.pending(course)
            if pending:
                raise CourseValidationError(
                    "Curso possui pendências para publicação: " + ", ".join(pending)
                )
            course.status = "published"
            course.published_at = datetime.now(UTC)
        else:
            course.status = "draft"
            course.published_at = None
        self.session.commit()
        self.session.refresh(course)
        return PublicationResponse(
            course_id=course.id, status=course.status, published_at=course.published_at
        )
