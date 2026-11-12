"""Remote references for real users, courses, lessons, and access."""
import os
from datetime import datetime, timezone
from uuid import UUID

import httpx
from fastapi import HTTPException, Request
from pydantic import BaseModel, StrictBool, ValidationError

from app.integrations import AuditEntry, Course, LessonRef, User


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
    moderation_status: str = "visible"


class Pagination(BaseModel):
    pages: int


class TeacherCoursesPage(BaseModel):
    items: list[CourseData]
    pagination: Pagination


class LessonSummary(BaseModel):
    id: UUID
    title: str
    position: int
    duration_seconds: float | None = None


class CourseLessons(BaseModel):
    course_id: UUID
    items: list[LessonSummary]


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

    def write(self, setting, path, data):
        base = os.getenv(setting, "").rstrip("/")
        service_token = os.getenv("INTERNAL_SERVICE_TOKEN", "")
        if not base or len(service_token) < 16:
            raise HTTPException(503, "Comando de moderação não configurado")
        try:
            with httpx.Client(timeout=4, trust_env=False, follow_redirects=False) as client:
                response = client.request("POST" if setting == "IDENTITY_URL" else "PUT", base + path,
                    json=data, headers={"Authorization": f"Bearer {self.access}",
                                        "X-Service-Token": service_token})
            if response.status_code in {401, 403, 404, 409}:
                raise HTTPException(response.status_code, "Comando remoto recusado")
            if response.status_code not in {200, 201}:
                raise HTTPException(503, "Comando remoto indisponível")
            return response.json()
        except (httpx.RequestError, ValueError) as exc:
            raise HTTPException(503, "Falha no comando de moderação") from exc

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
        return self._course(row)

    @staticmethod
    def _course(row: CourseData) -> Course:
        # A course hidden or deleted by moderation is not available to students,
        # even if its catalog status is still "published".
        published = row.status == "published" and row.moderation_status == "visible"
        return Course(str(row.id), row.title, str(row.teacher_id), row.teacher_name, published)

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
        """Courses of the authenticated teacher (catalog contract; teachers only)."""
        items, page, pages = [], 1, 1
        while page <= pages and page <= 50:
            data = self.read("CATALOG_URL", f"/api/teacher/courses/summary?page={page}&size=100",
                             TeacherCoursesPage)
            items.extend(self._course(row) for row in data.items)
            pages, page = data.pagination.pages, page + 1
        return items

    def course_lessons(self, course_id):
        try:
            course_id = str(UUID(course_id))
        except ValueError:
            return []
        data = self.read("LEARNING_URL", f"/api/learning/courses/{course_id}/lesson-summaries",
                         CourseLessons, missing=True)
        if data is None:
            return []
        if str(data.course_id) != course_id:
            raise HTTPException(503, "Curso divergente")
        return sorted((LessonRef(str(item.id), course_id, item.title, item.position,
                                 int(item.duration_seconds or 0)) for item in data.items),
                      key=lambda lesson: lesson.position)

    def course_engagement_snapshot(self, course_id, period):
        # Enrollment and completion belong to access/learning, which expose no
        # aggregate contract yet: report them as unavailable instead of failing.
        return {"enrollments": None, "active_students": None,
                "completion_rate": None, "avg_watch_minutes": None}

    def platform_snapshot(self, period):
        raise HTTPException(503, "Indicadores ainda não integrados")

    def apply_moderation(self, item_type, item_id, decision):
        if len(os.getenv("INTERNAL_SERVICE_TOKEN", "")) < 16:
            raise HTTPException(503, "Auditoria de moderação não configurada")
        try:
            item_id = str(UUID(item_id))
        except ValueError:
            raise HTTPException(404, "Conteúdo não encontrado") from None
        if item_type == "course":
            path, setting = f"/api/courses/{item_id}/moderation", "CATALOG_URL"
        elif item_type == "lesson":
            path, setting = f"/api/learning/lessons/{item_id}/moderation", "LEARNING_URL"
        else:
            raise HTTPException(400, "Tipo de moderação inválido")
        expected = {"keep":"visible", "hide":"hidden", "delete":"deleted"}[decision]
        result = self.write(setting, path, {"decision": decision})
        if not isinstance(result, dict) or result.get("moderation_status") != expected:
            raise HTTPException(503, "Proprietário não confirmou a decisão")

    def record_audit(self, admin_id, item_id, item_type, decision, justification, operation_id=None):
        if not operation_id:
            raise HTTPException(503, "Operação de auditoria sem identificador")
        response = self.write("IDENTITY_URL", "/api/v1/admin/audit/moderation",
            {"operation_id": operation_id, "item_type": item_type, "item_id": item_id,
             "decision": decision, "justification": justification})
        if not isinstance(response, dict) or response.get("recorded") is not True or not response.get("audit_id"):
            raise HTTPException(503, "Auditoria não confirmada")
        return AuditEntry(admin_id, item_id, item_type, decision, justification,
                          datetime.now(timezone.utc).isoformat())
