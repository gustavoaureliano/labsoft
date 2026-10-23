from __future__ import annotations

from contextlib import contextmanager
from typing import Callable

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Request,
    Response,
    UploadFile,
)

from fastapi.responses import FileResponse

from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .config import Settings
from .models import AuditEvent, AuthSession, User

from .schemas import (
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

from .services import (
    EmailSender,
    EmailOutboxService,
    IdentityService,
    MediaService,
    NotificationService,
    ProfileService,
    RateLimitService,
    ServiceError,
    SessionService,
    TeacherApplicationService,
)


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
            email, token = result
            email_outbox.enqueue(
                db,
                result[2],
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