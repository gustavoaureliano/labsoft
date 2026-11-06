from __future__ import annotations

import smtplib

from email.message import EmailMessage
from typing import Protocol

import httpx

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import Settings
from ..models import Notification, User, utcnow
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


class BrevoEmailSender:

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
            not settings.brevo_api_key
            or not settings.brevo_sender_email
        ):
            raise ServiceError(
                "unavailable",
                "Brevo não está configurado.",
            )

        response = httpx.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "api-key": settings.brevo_api_key,
                "accept": "application/json",
            },
            json={
                "sender": {
                    "name": settings.brevo_sender_name,
                    "email": settings.brevo_sender_email,
                },
                "to": [{"email": to}],
                "subject": subject,
                "textContent": body,
            },
            timeout=10,
        )
        if response.is_error:
            raise RuntimeError(
                f"Brevo returned HTTP {response.status_code}."
            )


def configured_email_sender(
    settings: Settings,
) -> EmailSender:
    if settings.brevo_api_key and settings.brevo_sender_email:
        return BrevoEmailSender(settings)
    return SMTPEmailSender(settings)


class NotificationService:

    def __init__(
        self,
        settings: Settings,
        email_sender: EmailSender | None = None,
    ):
        self.settings = settings
        self.email_sender = (
            email_sender or configured_email_sender(settings)
        )

    def check_email_available(self) -> None:
        if isinstance(self.email_sender, SMTPEmailSender) and (
            not self.settings.smtp_host or not self.settings.smtp_from
        ):
            raise ServiceError(
                "unavailable",
                "Recuperação por e-mail indisponível: "
                "configure Brevo ou SMTP.",
            )
        if isinstance(self.email_sender, BrevoEmailSender) and (
            not self.settings.brevo_api_key
            or not self.settings.brevo_sender_email
        ):
            raise ServiceError(
                "unavailable",
                "Recuperação por e-mail indisponível: "
                "configure Brevo ou SMTP.",
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

    def mark_read(
        self,
        db: Session,
        user: User,
        notification_id: str,
    ) -> Notification:

        notification = db.scalar(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user.id,
            )
        )

        if notification is None:
            raise ServiceError(
                "not_found",
                "Notificação não encontrada.",
            )

        if notification.read_at is None:
            notification.read_at = utcnow()

        db.flush()

        return notification