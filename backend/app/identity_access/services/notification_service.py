from __future__ import annotations

import smtplib

from email.message import EmailMessage
from typing import Protocol
from urllib.parse import quote

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import Settings
from ..models import Notification, User
from .errors import ServiceError


class EmailSender(Protocol):

    def send(
        self,
        to: str,
        subject: str,
        body: str,
    ) -> None:
        ...


class SMTPEmailSender:

    def __init__(
        self,
        settings: Settings,
    ):
        self.settings = settings

    def send(
        self,
        to: str,
        subject: str,
        body: str,
    ) -> None:

        settings = self.settings

        if (
            not settings.smtp_host
            or not settings.smtp_from
        ):
            raise ServiceError(
                "unavailable",
                "SMTP não configurado.",
            )

        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = settings.smtp_from
        message["To"] = to
        message.set_content(body)

        with smtplib.SMTP(
            settings.smtp_host,
            settings.smtp_port,
            timeout=10,
        ) as client:

            if settings.smtp_starttls:
                client.starttls()

            if (
                settings.smtp_username
                and settings.smtp_password
            ):
                client.login(
                    settings.smtp_username,
                    settings.smtp_password,
                )

            client.send_message(message)


class NotificationService:

    def __init__(
        self,
        settings: Settings,
        email_sender: EmailSender | None = None,
    ):
        self.settings = settings
        self.email_sender = (
            email_sender or SMTPEmailSender(settings)
        )

    def check_email_available(self) -> None:

        if (
            isinstance(
                self.email_sender,
                SMTPEmailSender,
            )
            and (
                not self.settings.smtp_host
                or not self.settings.smtp_from
            )
        ):
            raise ServiceError(
                "unavailable",
                "Recuperação por e-mail indisponível: "
                "configure SMTP.",
            )

    def send_recovery(
        self,
        email: str,
        token: str,
    ) -> None:

        reset_url = (
            self.settings.password_reset_url
            .split("#", 1)[0]
        )

        link = (
            reset_url
            + "#token="
            + quote(token, safe="")
        )

        self.email_sender.send(
            email,
            "AprovaAí - recuperação de acesso",
            (
                "Para redefinir sua senha, "
                "abra este link em até "
                f"{self.settings.reset_minutes} "
                "minutos:\n"
                f"{link}\n"
                "Se você não solicitou a recuperação, "
                "ignore a mensagem."
            ),
        )

    def add(
        self,
        db: Session,
        user_id: str,
        category: str,
        message: str,
        details: dict | None = None,
    ) -> Notification:

        notification = Notification(
            user_id=user_id,
            category=category,
            message=message,
            details=details or {},
        )

        db.add(notification)
        db.flush()

        return notification

    def list_for(
        self,
        db: Session,
        user: User,
    ) -> list[Notification]:

        return list(
            db.scalars(
                select(Notification)
                .where(
                    Notification.user_id == user.id
                )
                .order_by(
                    Notification.created_at.desc()
                )
                .limit(100)
            )
        )