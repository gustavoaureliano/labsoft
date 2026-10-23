from app.database import SessionLocal
from app.identity_access.config import Settings
from app.identity_access.services.email_outbox_service import (
    EmailOutboxService,
)
from app.identity_access.services.notification_service import (
    configured_email_sender,
)


def main() -> None:
    settings = Settings.from_env()
    worker = EmailOutboxService(settings)
    worker.run_worker(
        SessionLocal,
        configured_email_sender(settings),
    )


if __name__ == "__main__":
    main()
