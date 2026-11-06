from typing import Callable
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    FastAPI,
    Form,
    HTTPException,
    Request,
    Response,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_session as get_db
from app.identity_access import Settings
from app.identity_access.api import (
    AuthDependencies,
    _check_rate_limit,
    _record_audit,
    _require_allowed_origin,
    translate_service_error,
)
from app.identity_access.models import AuditEvent, AuthSession, User
from app.identity_access.schemas import (
    LoginIn,
    EmailVerificationIn,
    MediaOut,
    NotificationOut,
    PasswordRecoveryIn,
    PasswordResetIn,
    ProfileOut,
    ProfileUpdateIn,
    RegisterIn,
    StatusOut,
    SessionOut,
    TeacherApplicationIn,
    TeacherApplicationOut,
    TokenOut,
    UserRoleUpdateIn,
    UserStatusUpdateIn,
    UserOut,
)
from app.identity_access.services import (
    EmailSender,
    EmailOutboxService,
    IdentityService,
    MediaService,
    NotificationService,
    ProfileService,
    ServiceError,
    SessionService,
    TeacherApplicationService,
)


# INÍCIO DAS ROTAS TRANSFERIDAS DE identity_access/api.py.
# Centralizadas temporariamente na main.py para reorganização posterior.
def create_router(
    get_db: Callable,
    settings: Settings | None = None,
    email_sender: EmailSender | None = None,
) -> APIRouter:

    settings = settings or Settings.from_env()

    auth = AuthDependencies(get_db, settings)
    current_user = auth.user()

    identity = IdentityService()
    profiles = ProfileService()
    sessions = SessionService()

    notifications = NotificationService(
        settings,
        email_sender,
    )
    email_outbox = EmailOutboxService(settings)

    media_service = MediaService(settings)
    teacher_apps = TeacherApplicationService()

    router = APIRouter(
        prefix="/api/v1",
        tags=["Identity"],
    )

    # F02 - CADASTRO

    @router.post(
        "/auth/register",
        response_model=UserOut,
        status_code=201,
    )
    def register(
        body: RegisterIn,
        request: Request,
        db: Session = Depends(get_db),
    ):
        _check_rate_limit(
            db,
            request,
            "register",
            str(body.email),
            5,
            600,
        )
        try:
            with translate_service_error():
                notifications.check_email_available()
                user = identity.register(
                    db, body
                )

                profiles.create(
                    db,
                    user,
                    body.display_name,
                )
                token = identity.create_verification_token(
                    db,
                    user,
                    settings,
                )
                email_outbox.enqueue(
                    db,
                    user.id,
                    user.email,
                    "verify_email",
                    token,
                )
                _record_audit(
                    db,
                    request,
                    "user.registered",
                    "pending_verification",
                    subject_id=user.id,
                )

            db.commit()
            return user

        except IntegrityError as exc:
            db.rollback()

            raise HTTPException(
                status_code=409,
                detail="E-mail já cadastrado.",
            ) from exc

        except Exception:
            db.rollback()
            raise

    # F03 - LOGIN

    @router.post(
        "/auth/login",
        response_model=TokenOut,
    )
    def login(
        body: LoginIn,
        request: Request,
        response: Response,
        db: Session = Depends(get_db),
    ):
        _check_rate_limit(
            db,
            request,
            "login",
            str(body.email),
            10,
            900,
        )
        try:
            user = identity.authenticate(
                db,
                str(body.email),
                body.password,
            )
        except ServiceError as exc:
            _record_audit(
                db,
                request,
                "auth.login",
                "failure",
            )
            db.commit()
            raise HTTPException(
                status_code=401,
                detail="Credenciais inválidas.",
            ) from exc

        session_tokens = sessions.create(
            db,
            user,
            settings,
        )
        _record_audit(
            db,
            request,
            "auth.login",
            "success",
            actor_id=user.id,
            subject_id=user.id,
        )

        db.commit()
        response.set_cookie(
            key="aprovaai_refresh",
            value=session_tokens.refresh_token,
            max_age=settings.refresh_token_days * 24 * 60 * 60,
            httponly=True,
            secure=settings.cookie_secure,
            samesite=settings.cookie_samesite,
            path="/api/v1/auth",
        )
        response.headers["Cache-Control"] = "no-store"

        return TokenOut(
            access_token=session_tokens.access_token,
            expires_in_seconds=session_tokens.expires_in_seconds,
            user=UserOut.model_validate(user),
        )

    @router.post("/auth/verify-email", response_model=StatusOut)
    def verify_email(
        body: EmailVerificationIn,
        request: Request,
        db: Session = Depends(get_db),
    ):
        _check_rate_limit(
            db,
            request,
            "verify-email",
            body.token,
            10,
            3600,
        )
        with translate_service_error():
            user = identity.verify_email(
                db,
                body.token,
            )

        _record_audit(
            db,
            request,
            "user.email.verified",
            "success",
            actor_id=user.id,
            subject_id=user.id,
        )
        db.commit()
        return StatusOut(
            message="E-mail confirmado. Sua conta está ativa."
        )

    @router.post(
        "/auth/resend-verification",
        response_model=StatusOut,
        status_code=202,
    )
    def resend_verification(
        body: PasswordRecoveryIn,
        request: Request,
        db: Session = Depends(get_db),
    ):
        _check_rate_limit(
            db,
            request,
            "resend-verification",
            str(body.email),
            3,
            3600,
        )
        with translate_service_error():
            user = identity.find_pending_user(
                db,
                str(body.email),
            )
            if user is not None:
                token = identity.create_verification_token(
                    db,
                    user,
                    settings,
                )
                email_outbox.enqueue(
                    db,
                    user.id,
                    user.email,
                    "verify_email",
                    token,
                )
        db.commit()
        return StatusOut(
            message=(
                "Se a conta estiver pendente, "
                "um novo e-mail será enviado."
            )
        )

    @router.post("/auth/refresh", response_model=TokenOut)
    def refresh_session(
        request: Request,
        response: Response,
        db: Session = Depends(get_db),
    ):
        _require_allowed_origin(request, settings)
        _check_rate_limit(
            db,
            request,
            "refresh",
            request.cookies.get("aprovaai_refresh", "missing"),
            30,
            60,
        )
        raw_refresh_token = request.cookies.get("aprovaai_refresh")
        if not raw_refresh_token:
            raise HTTPException(
                status_code=401,
                detail="Refresh token ausente.",
            )
        with translate_service_error():
            session_tokens = sessions.refresh(
                db,
                raw_refresh_token,
                settings,
            )
            session = db.get(
                AuthSession,
                session_tokens.session_id,
            )
            user = db.get(User, session.user_id)
        db.commit()
        response.set_cookie(
            key="aprovaai_refresh",
            value=session_tokens.refresh_token,
            max_age=settings.refresh_token_days * 24 * 60 * 60,
            httponly=True,
            secure=settings.cookie_secure,
            samesite=settings.cookie_samesite,
            path="/api/v1/auth",
        )
        response.headers["Cache-Control"] = "no-store"
        return TokenOut(
            access_token=session_tokens.access_token,
            expires_in_seconds=session_tokens.expires_in_seconds,
            user=UserOut.model_validate(user),
        )

    # F03 - LOGOUT

    @router.post(
        "/auth/logout",
        response_model=StatusOut,
    )
    def logout(
        request: Request,
        response: Response,
        credentials: HTTPAuthorizationCredentials | None = Depends(
            auth.bearer
        ),
        db: Session = Depends(get_db),
    ):
        if credentials is not None:
            with translate_service_error():
                sessions.revoke(
                    db,
                    credentials.credentials,
                    settings,
                )
        else:
            _require_allowed_origin(request, settings)
            refresh_token = request.cookies.get("aprovaai_refresh")
            if not refresh_token:
                raise HTTPException(
                    status_code=401,
                    detail="Autenticação obrigatória.",
                )
            with translate_service_error():
                sessions.revoke_by_refresh_token(
                    db,
                    refresh_token,
                )

        _record_audit(
            db,
            request,
            "auth.logout",
            "success",
        )
        db.commit()
        response.delete_cookie(
            key="aprovaai_refresh",
            path="/api/v1/auth",
            httponly=True,
            secure=settings.cookie_secure,
            samesite=settings.cookie_samesite,
        )
        response.delete_cookie(
            key="aprovaai_admin_docs",
            path="/",
            httponly=True,
            secure=settings.cookie_secure,
            samesite=settings.cookie_samesite,
        )

        return StatusOut(
            message="Sessão encerrada."
        )

    @router.get("/auth/sessions", response_model=list[SessionOut])
    def list_sessions(
        user: User = Depends(current_user),
        db: Session = Depends(get_db),
    ):
        return [
            SessionOut.model_validate(session)
            for session in sessions.list_for_user(db, user.id)
        ]

    @router.delete("/auth/sessions/{session_id}", response_model=StatusOut)
    def revoke_session(
        session_id: str,
        user: User = Depends(current_user),
        db: Session = Depends(get_db),
    ):
        owned_session = next(
            (
                item
                for item in sessions.list_for_user(db, user.id)
                if item.id == session_id
            ),
            None,
        )
        if owned_session is None:
            raise HTTPException(
                status_code=404,
                detail="Sessão não encontrada.",
            )
        sessions.revoke_session(db, session_id)
        db.commit()
        return StatusOut(message="Sessão revogada.")

    @router.post("/auth/logout-all", response_model=StatusOut)
    def logout_all(
        response: Response,
        user: User = Depends(current_user),
        db: Session = Depends(get_db),
    ):
        sessions.revoke_all(db, user.id)
        db.commit()
        response.delete_cookie(
            key="aprovaai_refresh",
            path="/api/v1/auth",
            httponly=True,
            secure=settings.cookie_secure,
            samesite=settings.cookie_samesite,
        )
        response.delete_cookie(
            key="aprovaai_admin_docs",
            path="/",
            httponly=True,
            secure=settings.cookie_secure,
            samesite=settings.cookie_samesite,
        )
        return StatusOut(message="Todas as sessões foram encerradas.")

    @router.get(
        "/auth/me",
        response_model=UserOut,
    )
    def who_am_i(
        user: User = Depends(current_user),
    ):
        return user

    @router.patch(
        "/admin/users/{user_id}/role",
        response_model=UserOut,
    )
    def update_user_role(
        user_id: str,
        body: UserRoleUpdateIn,
        request: Request,
        actor: User = Depends(auth.roles("admin")),
        db: Session = Depends(get_db),
    ):
        with translate_service_error():
            user = identity.set_role(
                db,
                user_id,
                body.role,
            )
        _record_audit(
            db,
            request,
            "user.role.changed",
            "success",
            actor_id=actor.id,
            subject_id=user.id,
            details={"role": user.role},
        )
        db.commit()
        return user

    @router.patch(
        "/admin/users/{user_id}/status",
        response_model=UserOut,
    )
    def update_user_status(
        user_id: str,
        body: UserStatusUpdateIn,
        request: Request,
        actor: User = Depends(auth.roles("admin")),
        db: Session = Depends(get_db),
    ):
        with translate_service_error():
            user = identity.set_status(
                db,
                user_id,
                body.status,
            )
        _record_audit(
            db,
            request,
            "user.status.changed",
            "success",
            actor_id=actor.id,
            subject_id=user.id,
            details={"status": user.status},
        )
        db.commit()
        return user

    # F04 - SOLICITAR RECUPERACAO

    @router.post(
        "/auth/forgot-password",
        response_model=StatusOut,
        status_code=202,
    )
    @router.post(
        "/auth/password-recovery/request",
        response_model=StatusOut,
        status_code=202,
    )
    def request_recovery(
        body: PasswordRecoveryIn,
        request: Request,
        db: Session = Depends(get_db),
    ):
        _check_rate_limit(
            db,
            request,
            "forgot-password",
            str(body.email),
            3,
            3600,
        )
        with translate_service_error():
            notifications.check_email_available()

            result = identity.request_password_reset(
                db,
                str(body.email),
                settings,
            )

        if result:
            email, token, user_id = result
            email_outbox.enqueue(
                db,
                user_id,
                email,
                "password_reset",
                token,
            )
        db.commit()

        return StatusOut(
            message=(
                "Se o e-mail estiver cadastrado, "
                "você receberá instruções."
            )
        )

    # F04 - CONFIRMAR NOVA SENHA

    @router.post(
        "/auth/reset-password",
        response_model=StatusOut,
    )
    @router.post(
        "/auth/password-recovery/confirm",
        response_model=StatusOut,
    )
    def confirm_recovery(
        body: PasswordResetIn,
        db: Session = Depends(get_db),
    ):
        with translate_service_error():
            identity.reset_password(
                db,
                body.token,
                body.new_password,
            )

        db.commit()

        return StatusOut(
            message=(
                "Senha redefinida; entre novamente."
            )
        )

    # PERFIL

    @router.get(
        "/profiles/me",
        response_model=ProfileOut,
    )
    def get_profile(
        user: User = Depends(current_user),
        db: Session = Depends(get_db),
    ):
        with translate_service_error():
            return profiles.get(db, user)

    @router.patch(
        "/profiles/me",
        response_model=ProfileOut,
    )
    def edit_profile(
        body: ProfileUpdateIn,
        user: User = Depends(current_user),
        db: Session = Depends(get_db),
    ):
        with translate_service_error():
            obj = profiles.update(
                db,
                user,
                body,
            )

        db.commit()
        return obj

    # F05 - UPLOAD DE DOCUMENTOS

    @router.post(
        "/media/documents",
        response_model=MediaOut,
        status_code=201,
    )
    def upload_document(
        file: UploadFile = File(...),
        user: User = Depends(
            auth.roles("student")
        ),
        db: Session = Depends(get_db),
    ):
        saved = None

        try:
            with translate_service_error():
                saved = (
                    media_service.upload_document(
                        db,
                        user,
                        file,
                    )
                )

            db.commit()
            return saved

        except Exception:
            db.rollback()

            if saved is not None:
                (
                    settings.media_root.resolve()
                    / saved.storage_name
                ).unlink(missing_ok=True)

            raise

        finally:
            file.file.close()

    @router.get(
        "/media/documents/{document_id}"
    )
    def download_document(
        document_id: str,
        user: User = Depends(current_user),
        db: Session = Depends(get_db),
    ):
        with translate_service_error():
            metadata, path = (
                media_service.find_authorized(
                    db,
                    user,
                    document_id,
                )
            )

        return FileResponse(
            path,
            media_type="application/octet-stream",
            filename=metadata.original_name,
            content_disposition_type="attachment",
            headers={
                "X-Content-Type-Options": "nosniff",
                "Cache-Control": "no-store",
            },
        )

    def application_output(
        app,
    ) -> TeacherApplicationOut:

        return TeacherApplicationOut(
            id=app.id,
            user_id=app.user_id,
            legal_name=app.legal_name,
            professional_summary=(
                app.professional_summary
            ),
            expertise=app.expertise,
            status=app.status,
            created_at=app.created_at,
            document_ids=[
                file.id for file in app.documents
            ],
        )

    # F05 - SOLICITAR CADASTRO DE PROFESSOR

    @router.post(
        "/teacher-applications",
        response_model=TeacherApplicationOut,
        status_code=201,
    )
    def create_teacher_application(
        body: TeacherApplicationIn,
        user: User = Depends(
            auth.roles("student")
        ),
        db: Session = Depends(get_db),
    ):
        try:
            with translate_service_error():
                obj = teacher_apps.submit(
                    db,
                    user,
                    body,
                    notifications,
                )

            db.commit()
            return application_output(obj)

        except IntegrityError as exc:
            db.rollback()

            raise HTTPException(
                status_code=409,
                detail="Solicitação já existente.",
            ) from exc

        except Exception:
            db.rollback()
            raise

    @router.get(
        "/teacher-applications/me",
        response_model=TeacherApplicationOut,
    )
    def my_teacher_application(
        user: User = Depends(current_user),
        db: Session = Depends(get_db),
    ):
        with translate_service_error():
            obj = teacher_apps.get_mine(
                db,
                user,
            )

        return application_output(obj)

    # NOTIFICACOES

    @router.get(
        "/notifications/me",
        response_model=list[NotificationOut],
    )
    def my_notifications(
        user: User = Depends(current_user),
        db: Session = Depends(get_db),
    ):
        return notifications.list_for(
            db,
            user,
        )

    @router.patch(
        "/notifications/{notification_id}/read",
        response_model=NotificationOut,
    )
    def mark_notification_read(
        notification_id: str,
        user: User = Depends(current_user),
        db: Session = Depends(get_db),
    ):
        with translate_service_error():
            notification = notifications.mark_read(
                db,
                user,
                notification_id,
            )

        db.commit()
        return notification

    # F06 - TESTE DE AUTORIZACAO POR PERFIL

    @router.get("/auth/test/teacher")
    def teacher_only(
        user: User = Depends(auth.roles("teacher")),
    ):
        return {
            "teacher_id": user.id,
            "message": "Acesso autorizado",
        }

    return router


# FIM DAS ROTAS TRANSFERIDAS DE identity_access/api.py.

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
    # O formulário administrativo precisa preservar a origem no POST do navegador.
    response.headers["Referrer-Policy"] = (
        "same-origin"
        if request.method == "GET" and request.url.path == "/admin/login"
        else "no-referrer"
    )
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
            "Referrer-Policy": "same-origin",
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
