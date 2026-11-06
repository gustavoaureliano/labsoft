from __future__ import annotations

from contextlib import contextmanager
from typing import Callable

from fastapi import (
    Depends,
    HTTPException,
    Request,
)

from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from sqlalchemy.orm import Session

from .config import Settings
from .models import AuditEvent, User
from .services import IdentityService, RateLimitService, ServiceError, SessionService

_HTTP_CODES = {
    "invalid": 400,
    "unauthorized": 401,
    "forbidden": 403,
    "not_found": 404,
    "conflict": 409,
    "too_large": 413,
    "unavailable": 503,
    "rate_limited": 429,
}


def _require_allowed_origin(
    request: Request,
    settings: Settings,
) -> None:
    origin = request.headers.get("origin")
    api_origin = (
        f"{request.url.scheme}://{request.url.netloc}"
    )
    allowed_origins = {
        settings.frontend_origin.rstrip("/"),
        api_origin,
    }
    if origin not in allowed_origins:
        raise HTTPException(
            status_code=403,
            detail="Origem não autorizada.",
        )


def _check_rate_limit(
    db: Session,
    request: Request,
    scope: str,
    identity: str,
    limit: int,
    window_seconds: int,
) -> None:
    remote_ip = (
        request.client.host
        if request.client is not None
        else "unknown"
    )
    limiter = RateLimitService()
    ip_allowed = limiter.consume(
        db,
        f"{scope}:ip:{remote_ip}",
        limit,
        window_seconds,
    )
    identity_allowed = limiter.consume(
        db,
        f"{scope}:identity:{identity.strip().lower()}",
        limit,
        window_seconds,
    )
    db.commit()
    if not ip_allowed or not identity_allowed:
        raise HTTPException(
            status_code=429,
            detail="Limite de tentativas excedido. Tente novamente mais tarde.",
            headers={"Retry-After": str(window_seconds)},
        )


def _record_audit(
    db: Session,
    request: Request,
    event: str,
    outcome: str,
    actor_id: str | None = None,
    subject_id: str | None = None,
    details: dict | None = None,
) -> None:
    db.add(
        AuditEvent(
            actor_id=actor_id,
            subject_id=subject_id,
            event=event,
            outcome=outcome,
            request_id=getattr(
                request.state,
                "request_id",
                None,
            ),
            details=details or {},
        )
    )


@contextmanager
def translate_service_error():
    try:
        yield
    except ServiceError as exc:
        raise HTTPException(
            status_code=_HTTP_CODES.get(
                exc.code, 400
            ),
            detail=exc.detail,
        ) from exc


class AuthDependencies:

    def __init__(
        self,
        get_db: Callable,
        settings: Settings | None = None,
    ):
        self.get_db = get_db
        self.settings = settings or Settings.from_env()
        self.bearer = HTTPBearer(auto_error=False)
        self.sessions = SessionService()

    def user(self) -> Callable:

        get_db = self.get_db
        bearer = self.bearer
        settings = self.settings

        def resolve(
            db: Session = Depends(get_db),
            credentials: HTTPAuthorizationCredentials | None = Depends(
                bearer
            ),
        ) -> User:

            if credentials is None:
                raise HTTPException(
                    status_code=401,
                    detail="Autenticação obrigatória.",
                )

            with translate_service_error():
                return self.sessions.authenticate(
                    db,
                    credentials.credentials,
                    settings,
                )

            raise AssertionError("unreachable")

        return resolve

    def roles(
        self,
        *roles: str,
    ) -> Callable:

        resolve = self.user()

        def require_role(
            user: User = Depends(resolve),
        ) -> User:

            with translate_service_error():
                IdentityService.require_roles(
                    user,
                    *roles,
                )

            return user

        return require_role
