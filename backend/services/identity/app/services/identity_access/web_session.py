from fastapi import HTTPException, Request, Response

from .config import Settings

ACCESS_COOKIE = "aprovaai_access"


def require_web_origin(request: Request, settings: Settings) -> None:
    if request.headers.get("origin") != settings.frontend_origin.rstrip("/"):
        raise HTTPException(403, "Origem não autorizada.")


def access_credential(request: Request, settings: Settings) -> str:
    if "authorization" in request.headers:
        parts = request.headers["authorization"].split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(401, "Bearer inválido.")
        return parts[1]
    token = request.cookies.get(ACCESS_COOKIE)
    if not token:
        raise HTTPException(401, "Autenticação obrigatória.")
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        require_web_origin(request, settings)
    return token


def set_access_cookie(response: Response, token: str, lifetime: int, settings: Settings) -> None:
    response.set_cookie(ACCESS_COOKIE, token, max_age=lifetime, path="/api",
                        httponly=True, secure=settings.cookie_secure, samesite=settings.cookie_samesite)


def clear_access_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(ACCESS_COOKIE, path="/api", httponly=True,
                           secure=settings.cookie_secure, samesite=settings.cookie_samesite)
