from __future__ import annotations

import logging

from contextlib import contextmanager
from typing import Callable

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
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
from .models import User

from .schemas import (
    LoginIn,
    MediaOut,
    NotificationOut,
    PasswordRecoveryIn,
    PasswordResetIn,
    ProfileOut,
    ProfileUpdateIn,
    RegisterIn,
    StatusOut,
    TeacherApplicationIn,
    TeacherApplicationOut,
    TokenOut,
    UserOut,
)

from .services import (
    EmailSender,
    IdentityService,
    MediaService,
    NotificationService,
    ProfileService,
    ServiceError,
    SessionService,
    TeacherApplicationService,
)


logger = logging.getLogger(__name__)

_HTTP_CODES = {
    "invalid": 400,
    "unauthorized": 401,
    "forbidden": 403,
    "not_found": 404,
    "conflict": 409,
    "too_large": 413,
    "unavailable": 503,
}


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
    ):
        self.get_db = get_db
        self.bearer = HTTPBearer(
            auto_error=False
        )
        self.sessions = SessionService()

    def user(self) -> Callable:

        get_db = self.get_db
        bearer = self.bearer

        def resolve(
            db: Session = Depends(get_db),
            credentials: (
                HTTPAuthorizationCredentials | None
            ) = Depends(bearer),
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

    auth = AuthDependencies(get_db)
    current_user = auth.user()

    identity = IdentityService()
    profiles = ProfileService()
    sessions = SessionService()

    notifications = NotificationService(
        settings,
        email_sender,
    )

    media_service = MediaService(settings)
    teacher_apps = TeacherApplicationService()

    router = APIRouter(
        prefix="/api/v1",
        tags=["Identity / F02-F06"],
    )

    # F02 - CADASTRO

    @router.post(
        "/auth/register",
        response_model=UserOut,
        status_code=201,
    )
    def register(
        body: RegisterIn,
        db: Session = Depends(get_db),
    ):
        try:
            with translate_service_error():
                user = identity.register(
                    db, body
                )

                profiles.create(
                    db,
                    user,
                    body.display_name,
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
        db: Session = Depends(get_db),
    ):
        with translate_service_error():
            user = identity.authenticate(
                db,
                str(body.email),
                body.password,
            )

        token = sessions.create(
            db,
            user,
            settings,
        )

        db.commit()

        return TokenOut(
            access_token=token,
            expires_in_seconds=(
                settings.session_hours * 3600
            ),
            user=UserOut.model_validate(user),
        )

    # F03 - LOGOUT

    @router.post(
        "/auth/logout",
        response_model=StatusOut,
    )
    def logout(
        credentials: (
            HTTPAuthorizationCredentials | None
        ) = Depends(auth.bearer),
        db: Session = Depends(get_db),
    ):
        if credentials is None:
            raise HTTPException(
                status_code=401,
                detail="Autenticação obrigatória.",
            )

        with translate_service_error():
            sessions.revoke(
                db,
                credentials.credentials,
            )

        db.commit()

        return StatusOut(
            message="Sessão encerrada."
        )

    @router.get(
        "/auth/me",
        response_model=UserOut,
    )
    def who_am_i(
        user: User = Depends(current_user),
    ):
        return user

    # F04 - SOLICITAR RECUPERACAO

    @router.post(
        "/auth/password-recovery/request",
        response_model=StatusOut,
        status_code=202,
    )
    def request_recovery(
        body: PasswordRecoveryIn,
        db: Session = Depends(get_db),
    ):
        with translate_service_error():
            notifications.check_email_available()

            result = identity.request_password_reset(
                db,
                str(body.email),
                settings,
            )

        db.commit()

        if result:
            email, token = result

            try:
                notifications.send_recovery(
                    email, token
                )

            except Exception as exc:
                logger.exception(
                    "Falha ao enviar e-mail de recuperação"
                )

                raise HTTPException(
                    status_code=503,
                    detail=(
                        "Não foi possível enviar o "
                        "e-mail de recuperação."
                    ),
                ) from exc

        return StatusOut(
            message=(
                "Se o e-mail estiver cadastrado, "
                "você receberá instruções."
            )
        )

    # F04 - CONFIRMAR NOVA SENHA

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

    return router