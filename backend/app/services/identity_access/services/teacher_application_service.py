from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import (
    TeacherApplication,
    MediaItem,
    User,
)
from ..schemas import TeacherApplicationIn
from .errors import ServiceError
from .identity_service import IdentityService
from .notification_service import NotificationService


class TeacherApplicationService:

    def submit(
        self,
        db: Session,
        user: User,
        data: TeacherApplicationIn,
        notifications: NotificationService,
    ) -> TeacherApplication:

        IdentityService.require_roles(
            user, "student"
        )

        existing = db.scalar(
            select(TeacherApplication).where(
                TeacherApplication.user_id == user.id
            )
        )

        if existing:
            raise ServiceError(
                "conflict",
                "Já existe uma solicitação de professor "
                "para esta conta.",
            )

        media = list(
            db.scalars(
                select(MediaItem).where(
                    MediaItem.id.in_(
                        data.document_ids
                    )
                )
            )
        )

        if len(media) != len(data.document_ids):
            raise ServiceError(
                "invalid",
                "Um ou mais documentos "
                "não foram encontrados.",
            )

        if any(
            item.user_id != user.id
            or item.application_id is not None
            for item in media
        ):
            raise ServiceError(
                "forbidden",
                "Documento não pertence ao usuário "
                "ou já foi utilizado.",
            )

        application = TeacherApplication(
            user_id=user.id,
            legal_name=data.legal_name.strip(),
            professional_summary=(
                data.professional_summary.strip()
            ),
            expertise=data.expertise.strip(),
            status="pending",
        )

        db.add(application)
        db.flush()

        for item in media:
            item.application_id = application.id

        notifications.add(
            db,
            user.id,
            "teacher_application",
            "Sua solicitação de cadastro como "
            "professor está pendente de análise.",
            {
                "application_id": application.id,
                "status": "pending",
            },
        )

        db.flush()

        return application

    def get_mine(
        self,
        db: Session,
        user: User,
    ) -> TeacherApplication:

        application = db.scalar(
            select(TeacherApplication).where(
                TeacherApplication.user_id == user.id
            )
        )

        if application is None:
            raise ServiceError(
                "not_found",
                "Nenhuma solicitação encontrada.",
            )

        return application