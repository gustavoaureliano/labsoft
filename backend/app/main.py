from uuid import uuid4

from fastapi import (
    Depends,
    FastAPI,
    Form,
    HTTPException,
    Request,
    Response,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_session as get_db
from app.identity_access import (
    Settings,
    create_router,
)
from app.identity_access.api import (
    _check_rate_limit,
    translate_service_error,
)
from app.identity_access.models import AuditEvent, User
from app.identity_access.services import (
    IdentityService,
    ServiceError,
    SessionService,
)

settings = Settings.from_env()
app = FastAPI(
    title="AprovaAí API",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    allow_credentials=True,
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

app.include_router(
    create_router(
        get_db,
        settings,
    )
)


@app.middleware("http")
async def apply_security_headers(request: Request, call_next):
    request.state.request_id = str(uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Frame-Options"] = "DENY"
    if request.url.path.startswith("/api/v1/") or request.url.path in {
        "/docs",
        "/openapi.json",
        "/admin/login",
    }:
        response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/admin/login", include_in_schema=False)
def admin_docs_login_page() -> HTMLResponse:
    return HTMLResponse(
        """
        <!doctype html>
        <html lang="pt-BR">
          <head><meta charset="utf-8"><title>Login administrativo</title></head>
          <body>
            <main>
              <h1>Acesso administrativo à documentação</h1>
              <form method="post" action="/admin/login">
                <label>E-mail <input name="email" type="email" required></label>
                <label>Senha <input name="password" type="password" required></label>
                <button type="submit">Entrar</button>
              </form>
            </main>
          </body>
        </html>
        """,
        headers={
            "Cache-Control": "no-store",
            "Referrer-Policy": "no-referrer",
            "X-Content-Type-Options": "nosniff",
        },
    )


@app.post("/admin/login", include_in_schema=False)
def admin_docs_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
) -> Response:
    _require_origin(request)
    _check_rate_limit(
        db,
        request,
        "admin-docs-login",
        email,
        5,
        900,
    )
    identity = IdentityService()
    sessions = SessionService()
    with translate_service_error():
        try:
            user = identity.authenticate(db, email, password)
        except ServiceError as exc:
            db.add(
                AuditEvent(
                    event="admin_docs.login",
                    outcome="failure",
                    request_id=request.state.request_id,
                )
            )
            db.commit()
            raise HTTPException(
                status_code=401,
                detail="Credenciais inválidas.",
            ) from exc
    if user.role != "admin":
        db.add(
            AuditEvent(
                subject_id=user.id,
                event="admin_docs.login",
                outcome="failure",
                request_id=request.state.request_id,
            )
        )
        db.commit()
        raise HTTPException(
            status_code=403,
            detail="A documentação é restrita a administradores.",
        )
    session_tokens = sessions.create(db, user, settings)
    docs_token = sessions.create_admin_docs_token(
        user,
        session_tokens.session_id,
        settings,
    )
    db.add(
        AuditEvent(
            actor_id=user.id,
            subject_id=user.id,
            event="admin_docs.login",
            outcome="success",
            request_id=request.state.request_id,
        )
    )
    db.commit()
    redirect = RedirectResponse(
        url="/docs",
        status_code=303,
        headers={
            "Cache-Control": "no-store",
            "Referrer-Policy": "no-referrer",
        },
    )
    redirect.set_cookie(
        key="aprovaai_admin_docs",
        value=docs_token,
        max_age=settings.access_token_minutes * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        path="/",
    )
    redirect.set_cookie(
        key="aprovaai_refresh",
        value=session_tokens.refresh_token,
        max_age=settings.refresh_token_days * 24 * 60 * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        path="/api/v1/auth",
    )
    return redirect


def _require_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    request_origin = f"{request.url.scheme}://{request.url.netloc}"
    if origin not in {
        settings.frontend_origin.rstrip("/"),
        request_origin,
    }:
        raise HTTPException(
            status_code=403,
            detail="Origem não autorizada.",
        )


def _admin_docs_user(
    request: Request,
    db: Session,
) -> User:
    token = request.cookies.get("aprovaai_admin_docs")
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Autenticação administrativa obrigatória.",
        )
    try:
        return SessionService().authenticate_admin_docs(
            db,
            token,
            settings,
        )
    except ServiceError as exc:
        raise HTTPException(
            status_code=403,
            detail=exc.detail,
        ) from exc


@app.get("/docs", include_in_schema=False)
def admin_swagger_docs(
    request: Request,
    db: Session = Depends(get_db),
) -> Response:
    try:
        user = _admin_docs_user(request, db)
    except HTTPException as exc:
        if exc.status_code in {401, 403}:
            return RedirectResponse(
                "/admin/login",
                status_code=303,
                headers={"Cache-Control": "no-store"},
            )
        raise
    db.add(
        AuditEvent(
            actor_id=user.id,
            subject_id=user.id,
            event="admin_docs.access",
            outcome="success",
            request_id=request.state.request_id,
        )
    )
    db.commit()
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="AprovaAí API — ADMIN",
        swagger_ui_parameters={"persistAuthorization": False},
    )


@app.get("/openapi.json", include_in_schema=False)
def admin_openapi(
    request: Request,
    db: Session = Depends(get_db),
) -> JSONResponse:
    user = _admin_docs_user(request, db)
    db.add(
        AuditEvent(
            actor_id=user.id,
            subject_id=user.id,
            event="admin_openapi.access",
            outcome="success",
            request_id=request.state.request_id,
        )
    )
    db.commit()
    schema = get_openapi(
        title=app.title,
        version="1.0.0",
        routes=app.routes,
    )
    return JSONResponse(
        schema,
        headers={
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )
