import os
from uuid import UUID
from typing import Literal

import httpx
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

app = FastAPI(title="Servico de Acesso")


@app.middleware("http")
async def private_responses(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "private, no-store"
    response.headers.setdefault("Vary", "Cookie, Authorization")
    return response


class Identity(BaseModel):
    id: UUID
    role: Literal["student", "teacher", "admin"]


class Enrollment(BaseModel):
    course_id: UUID
    status: Literal["active", "cancelled", "past_due"]


class Subscriptions(BaseModel):
    user_id: UUID
    items: list[Enrollment]


def credential(request: Request) -> str:
    if "authorization" in request.headers:
        parts = request.headers["authorization"].split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(401, "Bearer inválido")
        return parts[1]
    token = request.cookies.get("aprovaai_access")
    if not token:
        raise HTTPException(401, "Autenticação obrigatória")
    return token


async def read(client, setting, path, token, schema):
    base = os.getenv(setting, "").rstrip("/")
    if not base:
        raise HTTPException(503, "Dependência não configurada")
    try:
        response = await client.get(base + path, headers={"Authorization": f"Bearer {token}"})
        if response.status_code == 401:
            raise HTTPException(401, "Sessão inválida")
        if response.status_code != 200:
            raise HTTPException(503, "Dependência indisponível")
        return schema.model_validate(response.json())
    except (httpx.RequestError, ValueError) as exc:
        raise HTTPException(503, "Falha na dependência de acesso") from exc


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/access")
async def check_access(course_id: UUID, request: Request) -> dict:
    """Commercial entitlement only; content owners also check publication/media."""
    if set(request.query_params) != {"course_id"}:
        raise HTTPException(422, "Informe somente course_id; usuário vem da sessão")
    token = credential(request)
    async with httpx.AsyncClient(timeout=4, trust_env=False, follow_redirects=False) as client:
        user = await read(client, "IDENTITY_URL", "/api/v1/auth/me", token, Identity)
        if user.role != "student":
            raise HTTPException(403, "Consulta exclusiva do aluno")
        subscriptions = await read(client, "SUBSCRIPTION_URL", "/api/subscriptions/me", token, Subscriptions)
    if subscriptions.user_id != user.id:
        raise HTTPException(503, "Usuário divergente na resposta de matrícula")
    allowed = any(item.course_id == course_id and item.status == "active" for item in subscriptions.items)
    return {
        "user_id": str(user.id), "course_id": str(course_id), "allowed": allowed,
        "reason": "free_enrollment" if allowed else "no_active_enrollment",
    }
