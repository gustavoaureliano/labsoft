"""Course lookup through the canonical catalog API."""
import os
from uuid import UUID
from typing import Literal

import httpx
from fastapi import HTTPException
from pydantic import BaseModel

from app.identity import access_credential
from app.integrations import Course, get_current_user


class CourseLookup(BaseModel):
    id: UUID
    teacher_id: UUID
    teacher_name: str
    title: str
    status: Literal["draft", "published", "archived"]
    cover_url: str | None = None


class CatalogIntegrations:
    def __init__(self, request):
        self.request = request
        self.token = access_credential(request) if request and ("authorization" in request.headers or request.cookies.get("aprovaai_access")) else None

    def read(self, setting, path, *, missing=False):
        base = os.getenv(setting, "").rstrip("/")
        if not base: raise HTTPException(503, "Integração não configurada")
        try:
            with httpx.Client(timeout=4, trust_env=False, follow_redirects=False) as client:
                response = client.get(base + path, headers={"Authorization": f"Bearer {self.token}"} if self.token else {})
            if missing and response.status_code == 404: return None
            if response.status_code in {401,403}: raise HTTPException(response.status_code, "Consulta não autorizada")
            if response.status_code != 200: raise HTTPException(503, "Dependência indisponível")
            return response.json()
        except (httpx.RequestError, ValueError) as exc: raise HTTPException(503, "Falha na integração HTTP") from exc

    @staticmethod
    def convert(data):
        try: row = CourseLookup.model_validate(data)
        except ValueError as exc: raise HTTPException(503, "Resposta de curso inválida") from exc
        return Course(str(row.id), row.title, str(row.teacher_id), row.cover_url or "/images/courses/fisica-quantica.webp", row.teacher_name, row.status == "published")

    def course(self, course_id):
        try: canonical = str(UUID(course_id))
        except ValueError: return None
        data = self.read("CATALOG_URL", f"/api/courses/{canonical}/summary", missing=True)
        if data is None: return None
        result = self.convert(data)
        if result.id != canonical: raise HTTPException(503, "Curso divergente")
        return result

    def courses(self):
        if self.request is None: raise HTTPException(401, "Usuário obrigatório")
        user = getattr(self.request.state, "current_user", None) or get_current_user(self.request)
        if user.role != "teacher":
            raise HTTPException(503, "Listagem de matrículas ainda não integrada")
        page, result = 1, []
        while True:
            data = self.read("CATALOG_URL", f"/api/teacher/courses/summary?page={page}&size=20")
            try:
                pagination = data["pagination"]
                if pagination["page"] != page or not isinstance(pagination["pages"], int): raise ValueError("Invalid page")
                result.extend(self.convert(item) for item in data["items"])
                if page >= pagination["pages"]: return result
                page += 1
            except (KeyError, TypeError, ValueError) as exc: raise HTTPException(503, "Paginação inválida") from exc

    def has_access(self, student_id, course_id):
        raise HTTPException(503, "Direito de acesso ainda não integrado")

    def access_status(self, student_id, course_id):
        raise HTTPException(503, "Direito de acesso ainda não integrado")

    def recommendations(self, student_id): return []
    def notifications(self, user_id): return []
    def notify_certificate(self, user_id, certificate_id):
        raise HTTPException(503, "Notificações ainda não integradas")
