"""Identity validation over HTTP; no access to identity's database or signing key."""
import math
import os
from typing import Literal
from urllib.parse import urlsplit
from uuid import UUID

import httpx
from fastapi import HTTPException, Request
from pydantic import BaseModel, Field, ValidationError


class IdentityResponse(BaseModel):
    id: UUID
    role: Literal["student", "teacher", "admin"]


class ProfileResponse(BaseModel):
    user_id: UUID
    display_name: str = Field(min_length=1)


def access_credential(request: Request) -> str:
    if "authorization" in request.headers:
        parts = request.headers["authorization"].split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(401, "Bearer inválido")
        return parts[1]
    token = request.cookies.get("aprovaai_access")
    if not token:
        raise HTTPException(401, "Autenticação obrigatória")
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        origin = os.environ.get("FRONTEND_ORIGIN", "").rstrip("/")
        if not origin:
            raise HTTPException(503, "Origem do frontend não configurada")
        if request.headers.get("origin") != origin:
            raise HTTPException(403, "Origem não autorizada")
    return token


def resolve_identity(request: Request) -> tuple[str, str, str]:
    token = access_credential(request)
    base = os.environ.get("IDENTITY_URL", "").rstrip("/")
    parsed = urlsplit(base)
    try:
        timeout = float(os.environ.get("IDENTITY_TIMEOUT_SECONDS", "3"))
    except ValueError as exc:
        raise HTTPException(503, "Timeout de identidade inválido") from exc
    if (parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username
            or parsed.query or parsed.fragment or not math.isfinite(timeout) or timeout <= 0):
        raise HTTPException(503, "Integração de identidade não configurada corretamente")

    def read(client, path, model):
        response = client.get(base + path, headers={"Authorization": f"Bearer {token}"})
        if response.status_code == 401:
            raise HTTPException(401, "Sessão inválida ou expirada")
        if response.status_code != 200:
            raise HTTPException(503, "Identidade indisponível")
        return model.model_validate(response.json())

    try:
        with httpx.Client(timeout=timeout, follow_redirects=False, trust_env=False) as client:
            user = read(client, "/api/v1/auth/me", IdentityResponse)
            profile = read(client, "/api/v1/profiles/me", ProfileResponse)
        if profile.user_id != user.id:
            raise HTTPException(503, "Perfil divergente da identidade")
    except (httpx.RequestError, ValueError, ValidationError) as exc:
        raise HTTPException(503, "Falha ao consultar identidade") from exc
    return str(user.id), user.role, profile.display_name
