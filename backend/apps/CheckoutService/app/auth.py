import os
from uuid import UUID
from typing import Literal

import httpx
from fastapi import HTTPException, Request
from pydantic import BaseModel


class Identity(BaseModel):
    id: UUID
    role: Literal["student", "teacher", "admin"]


class Course(BaseModel):
    id: UUID
    status: Literal["draft", "published", "archived"]
    access_type: Literal["free", "paid"]
    price: str | None


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


def read(setting: str, path: str, token: str | None, model):
    base = os.getenv(setting, "").rstrip("/")
    if not base:
        raise HTTPException(503, "Dependência não configurada")
    try:
        with httpx.Client(timeout=4, follow_redirects=False, trust_env=False) as client:
            response = client.get(base + path, headers={"Authorization": f"Bearer {token}"} if token else {})
        if response.status_code in (401, 403, 404):
            raise HTTPException(response.status_code, "Consulta remota recusada")
        if response.status_code != 200:
            raise HTTPException(503, "Dependência indisponível")
        return model.model_validate(response.json())
    except (httpx.RequestError, ValueError) as exc:
        raise HTTPException(503, "Contrato remoto inválido") from exc


def student(request: Request):
    access = credential(request)
    user = read("IDENTITY_URL", "/api/v1/auth/me", access, Identity)
    if user.role != "student":
        raise HTTPException(403, "Compra exclusiva do aluno")
    return user.id, access
