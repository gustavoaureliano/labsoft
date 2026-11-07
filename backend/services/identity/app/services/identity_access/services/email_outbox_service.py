from __future__ import annotations

import logging
import time
from datetime import timedelta
from urllib.parse import quote

from cryptography.fernet import Fernet
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import Settings
from ..models import EmailOutbox, utcnow
from .errors import ServiceError
from .notification_service import EmailSender


logger = logging.getLogger(__name__)


class EmailOutboxService:
    _MAX_ATTEMPTS = 8

    def __init__(self, settings: Settings):
        self.settings = settings
        if not settings.email_encryption_key:
            raise ServiceError(
                "unavailable",
                "Configure AA_EMAIL_ENCRYPTION_KEY para ativar a fila de e-mail.",
            )
        self._fernet = Fernet(
            settings.email_encryption_key.encode("ascii")
        )

    def enqueue(
        self,
        db: Session,
        user_id: str,
        recipient: str,
        purpose: str,
        token: str,
    ) -> None:
        if purpose not in {"verify_email", "password_reset"}:
            raise ValueError("Unsupported email purpose.")
        encrypted_token = self._fernet.encrypt(
            token.encode("utf-8")
        ).decode("ascii")
        db.add(
            EmailOutbox(
                user_id=user_id,
                recipient=recipient,
                purpose=purpose,
                encrypted_token=encrypted_token,
            )
        )

    def deliver_one(
        self,
        db: Session,
        sender: EmailSender,
    ) -> bool:
        now = utcnow()
        message = db.scalar(
            select(EmailOutbox)
            .where(
                EmailOutbox.status == "pending",
                EmailOutbox.next_attempt_at <= now,
            )
            .order_by(EmailOutbox.created_at)
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        if message is None:
            return False

        try:
            token = self._fernet.decrypt(
                message.encrypted_token.encode("ascii")
            ).decode("utf-8")
            subject, body = self._content(
                message.purpose,
                token,
            )
            sender.send(
                message.recipient,
                subject,
                body,
            )
        except Exception as exc:
            message.attempts += 1
            message.last_error = (
                f"Delivery failed ({type(exc).__name__})."
            )
            if message.attempts >= self._MAX_ATTEMPTS:
                message.status = "failed"
            else:
                delay_seconds = min(
                    60 * (2 ** (message.attempts - 1)),
                    24 * 60 * 60,
                )
                message.next_attempt_at = now + timedelta(
                    seconds=delay_seconds
                )
            logger.warning(
                "Transactional email delivery failed for outbox item %s.",
                message.id,
            )
            db.commit()
            return True

        message.status = "delivered"
        message.delivered_at = now
        message.encrypted_token = ""
        message.last_error = None
        db.commit()
        return True

    def run_worker(
        self,
        session_factory,
        sender: EmailSender,
        poll_seconds: float = 2,
    ) -> None:
        while True:
            with session_factory() as db:
                delivered_or_retried = self.deliver_one(db, sender)
            if not delivered_or_retried:
                time.sleep(poll_seconds)

    def _content(
        self,
        purpose: str,
        token: str,
    ) -> tuple[str, str]:
        if purpose == "verify_email":
            link = (
                f"{self.settings.public_app_url}/verificar-email"
                f"?token={quote(token, safe='')}"
            )
            return (
                "AprovaAí - confirme seu e-mail",
                (
                    "Para ativar sua conta, confirme seu e-mail "
                    f"em até {self.settings.verification_hours} horas:\n"
                    f"{link}\n"
                    "Se você não criou esta conta, ignore esta mensagem."
                ),
            )

        reset_url = self.settings.password_reset_url.split("#", 1)[0]
        link = f"{reset_url}#token={quote(token, safe='')}"
        return (
            "AprovaAí - recuperação de acesso",
            (
                "Para redefinir sua senha, abra este link em até "
                f"{self.settings.reset_minutes} minutos:\n"
                f"{link}\n"
                "Se você não solicitou a recuperação, ignore esta mensagem."
            ),
        )
