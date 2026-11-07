"""Remote references for real users, courses, lessons, and access."""
import os
from uuid import UUID

import httpx
from fastapi import HTTPException, Request
from pydantic import BaseModel, StrictBool, ValidationError

from app.integrations import Course, LessonRef, User


class Identity(BaseModel):
    id: UUID
    role: str


class Profile(BaseModel):
    user_id: UUID
    display_name: str


class CourseData(BaseModel):
    id: UUID
    teacher_id: UUID
    teacher_name: str
    title: str
    status: str


class LessonData(BaseModel):
    id: UUID
    course_id: UUID
    title: str
    position: int
    duration_seconds: float | None = None


class Decision(BaseModel):
    user_id: UUID
    course_id: UUID
    allowed: StrictBool


def credential(request: Request):
    if "authorization" in request.headers:
        parts = request.headers["authorization"].split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(401, "Bearer inválido")
        return parts[1]
    value = request.cookies.get("aprovaai_access")
    if not value:
        raise HTTPException(401, "Autenticação obrigatória")
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        origin = os.getenv("FRONTEND_ORIGIN", "").rstrip("/")
        if not origin:
            raise HTTPException(503, "Origem não configurada")
        if request.headers.get("origin") != origin:
            raise HTTPException(403, "Origem não autorizada")
    return value


class RemoteIntegrations:
    def __init__(self, request: Request):
        self.access = credential(request)
        self._user = None

    def read(self, setting, path, model, *, missing=False):
        base = os.getenv(setting, "").rstrip("/")
        if not base:
            raise HTTPException(503, "Dependência não configurada")
        try:
            with httpx.Client(timeout=4, trust_env=False, follow_redirects=False) as client:
                response = client.get(base + path, headers={"Authorization": f"Bearer {self.access}"})
            if response.status_code in {403, 404} and missing:
                return None
            if response.status_code == 401:
                raise HTTPException(401, "Sessão inválida")
            if response.status_code == 403:
                raise HTTPException(403, "Recurso não autorizado")
            if response.status_code != 200:
                raise HTTPException(503, "Dependência indisponível")
            return model.model_validate(response.json())
        except (httpx.RequestError, ValueError, ValidationError) as exc:
            raise HTTPException(503, "Contrato remoto inválido") from exc

    def current_user(self):
        if self._user is None:
            identity = self.read("IDENTITY_URL", "/api/v1/auth/me", Identity)
            profile = self.read("IDENTITY_URL", "/api/v1/profiles/me", Profile)
            if identity.id != profile.user_id or identity.role not in {"student", "teacher", "admin"}:
                raise HTTPException(503, "Identidade divergente")
            self._user = User(str(identity.id), identity.role, profile.display_name)
        return self._user

    def user(self, user_id):
        user = self.current_user()
        return user if user.id == user_id else None

    def course(self, course_id):
        try:
            course_id = str(UUID(course_id))
        except ValueError:
            return None
        row = self.read("CATALOG_URL", f"/api/courses/{course_id}/summary", CourseData, missing=True)
        if row is None:
            return None
        if str(row.id) != course_id:
            raise HTTPException(503, "Curso divergente")
        return Course(course_id, row.title, str(row.teacher_id), row.teacher_name, row.status == "published")

    def lesson(self, lesson_id):
        try:
            lesson_id = str(UUID(lesson_id))
        except ValueError:
            return None
        row = self.read("LEARNING_URL", f"/api/learning/lessons/{lesson_id}/summary", LessonData, missing=True)
        if row is None:
            return None
        if str(row.id) != lesson_id:
            raise HTTPException(503, "Aula divergente")
        return LessonRef(lesson_id, str(row.course_id), row.title, row.position, int(row.duration_seconds or 0))

    def has_access(self, student_id, course_id):
        try:
            course_id = str(UUID(course_id))
        except ValueError:
            raise HTTPException(404, "Curso inexistente") from None
        row = self.read("ACCESS_URL", f"/api/access?course_id={course_id}", Decision)
        if str(row.user_id) != student_id or str(row.course_id) != course_id:
            raise HTTPException(503, "Decisão divergente")
        return row.allowed

    def load_lesson_in_context(self, lesson_id, sequence):
        lesson = self.lesson(lesson_id)
        if lesson is None:
            raise KeyError("Aula não encontrada")
        course = self.course(lesson.course_id)
        index = sequence.index(lesson_id)
        return {"lesson_id": lesson_id, "title": lesson.title, "course_id": lesson.course_id,
                "course_title": course.title if course else "", "duration_seconds": lesson.duration_seconds,
                "previous_lesson_id": sequence[index-1] if index else None,
                "next_lesson_id": sequence[index+1] if index+1 < len(sequence) else None, "sequence": sequence}

    def courses(self):
        raise HTTPException(503, "Indicadores de cursos ainda não integrados")

    def course_lessons(self, course_id):
        raise HTTPException(503, "Indicadores de aulas ainda não integrados")

    def course_engagement_snapshot(self, course_id, period):
        raise HTTPException(503, "Indicadores ainda não integrados")

    def platform_snapshot(self, period):
        raise HTTPException(503, "Indicadores ainda não integrados")

    def record_audit(self, admin_id, item_id, item_type, decision, justification):
        raise HTTPException(503, "Auditoria remota ainda não integrada")
