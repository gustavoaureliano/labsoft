import os
from typing import Literal
from uuid import UUID

import httpx
from fastapi import HTTPException, Request
from pydantic import BaseModel


class Identity(BaseModel):
    id: UUID
    role: Literal["student", "teacher", "admin"]


def credential(request: Request) -> str:
    if "authorization" in request.headers:
        parts = request.headers["authorization"].split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(401, "Bearer inválido")
        return parts[1]
    access = request.cookies.get("aprovaai_access")
    if not access:
        raise HTTPException(401, "Autenticação obrigatória")
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        origin = os.getenv("FRONTEND_ORIGIN", "").rstrip("/")
        if not origin:
            raise HTTPException(503, "Origem não configurada")
        if request.headers.get("origin") != origin:
            raise HTTPException(403, "Origem não autorizada")
    return access


def remote(setting: str, path: str, access: str):
    base = os.getenv(setting, "").rstrip("/")
    if not base:
        raise HTTPException(503, "Dependência não configurada")
    try:
        with httpx.Client(timeout=4, trust_env=False, follow_redirects=False) as client:
            response = client.get(base + path, headers={"Authorization": f"Bearer {access}"})
        if response.status_code in {401, 403, 404}:
            raise HTTPException(response.status_code, "Consulta remota recusada")
        if response.status_code != 200:
            raise HTTPException(503, "Dependência indisponível")
        return response.json()
    except (httpx.RequestError, ValueError) as exc:
        raise HTTPException(503, "Falha na integração HTTP") from exc


def student(request: Request):
    access = credential(request)
    try:
        user = Identity.model_validate(remote("IDENTITY_URL", "/api/v1/auth/me", access))
    except ValueError as exc:
        raise HTTPException(503, "Identidade inconsistente") from exc
    if user.role != "student":
        raise HTTPException(403, "Ação exclusiva do aluno")
    return user.id, access
