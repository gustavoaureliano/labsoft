from __future__ import annotations

import getpass
import sys

from sqlalchemy import select

from app.database import SessionLocal
from app.identity_access.models import Profile, User, utcnow
from app.identity_access.security import hash_password
from app.identity_access.schemas import RegisterIn


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: python -m app.identity_access.bootstrap_admin EMAIL"
        )

    email = sys.argv[1].strip().lower()
    display_name = input("Nome do administrador: ").strip()
    password = getpass.getpass("Senha (mínimo 12 caracteres): ")
    confirmation = getpass.getpass("Confirme a senha: ")
    if password != confirmation:
        raise SystemExit("As senhas não correspondem.")

    data = RegisterIn(
        email=email,
        display_name=display_name,
        password=password,
    )

    with SessionLocal.begin() as db:
        existing_admin = db.scalar(
            select(User.id).where(User.role == "admin").limit(1)
        )
        if existing_admin is not None:
            raise SystemExit(
                "Já existe um administrador; use a rota administrativa de papéis."
            )

        user = User(
            email=str(data.email),
            password_hash=hash_password(data.password),
            role="admin",
            is_active=True,
            status="active",
            verified_at=utcnow(),
        )
        db.add(user)
        db.flush()
        db.add(
            Profile(
                user_id=user.id,
                display_name=data.display_name.strip(),
                preferences={},
            )
        )

    print("Administrador inicial criado.")


if __name__ == "__main__":
    main()
