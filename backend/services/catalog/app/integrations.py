"""HTTP identity and learning boundaries used by catalog routes."""
import math
import os
from uuid import UUID

import httpx
from fastapi import HTTPException, Request


def demo_mode():
    return os.getenv("CATALOG_DEMO_MODE", "false").lower() == "true" and not os.getenv("IDENTITY_URL")


def token(request: Request, required=True):
    if "authorization" in request.headers:
        parts = request.headers["authorization"].split()
        if len(parts) != 2 or parts[0].lower() != "bearer": raise HTTPException(401, "Bearer inválido")
        return parts[1]
    value = request.cookies.get("aprovaai_access")
    if value and request.method not in {"GET", "HEAD", "OPTIONS"}:
        origin = os.getenv("FRONTEND_ORIGIN", "").rstrip("/")
        if not origin: raise HTTPException(503, "Origem não configurada")
        if request.headers.get("origin") != origin: raise HTTPException(403, "Origem não autorizada")
    if required and not value: raise HTTPException(401, "Autenticação obrigatória")
    return value


def remote(service, path, access_token):
    base = os.getenv(service, "").rstrip("/")
    if not base: raise HTTPException(503, "Dependência não configurada")
    try:
        with httpx.Client(timeout=4, trust_env=False, follow_redirects=False) as client:
            r = client.get(base + path, headers={"Authorization": f"Bearer {access_token}"} if access_token else {})
        if r.status_code in {401, 403, 404}: raise HTTPException(r.status_code, "Consulta remota recusada")
        if r.status_code != 200: raise HTTPException(503, "Dependência indisponível")
        return r.json()
    except (httpx.RequestError, ValueError) as exc:
        raise HTTPException(503, "Resposta remota indisponível") from exc


def principal(request: Request):
    access = token(request)
    user = remote("IDENTITY_URL", "/api/v1/auth/me", access)
    profile = remote("IDENTITY_URL", "/api/v1/profiles/me", access)
    try:
        uid = UUID(user["id"])
        if user["role"] not in {"teacher", "student", "admin"} or UUID(profile["user_id"]) != uid:
            raise ValueError("Invalid identity")
        return uid, user["role"], str(profile["display_name"])
    except (KeyError, ValueError, TypeError) as exc: raise HTTPException(503, "Identidade inconsistente") from exc


def read_lesson_summaries(course_id, access):
    from app.courses.schemas import LessonResponse
    data = remote("LEARNING_URL", f"/api/learning/courses/{course_id}/lesson-summaries", access)
    try:
        if UUID(data["course_id"]) != course_id: raise ValueError("Wrong course")
        return [LessonResponse(id=row["id"], course_id=course_id, title=row["title"], summary=row.get("description", ""),
            position=row["position"], duration_minutes=math.ceil((row["duration_seconds"] or 0) / 60),
            section_title=row.get("section_title", "Aulas do curso"),
            video_media_id=None, preview_available=False) for row in data["items"]]
    except (KeyError, ValueError, TypeError) as exc: raise HTTPException(503, "Resposta de aulas inválida") from exc


def lesson_reader(request: Request):
    if demo_mode(): return None
    access = token(request)
    return lambda course_id: read_lesson_summaries(course_id, access)
