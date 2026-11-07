"""Explicit local-only verified accounts for the integrated development seed."""

import os
import json
import sys

from sqlalchemy import select, text

from app.database import SessionLocal, engine
from app.services.identity_access.models import Profile, User
from app.services.identity_access.security import hash_password
from app.services.identity_access.config import Settings
from app.services.identity_access.services.session_service import SessionService


def main():
    password = os.environ.get("APROVAAI_LOCAL_SEED_PASSWORD", "")
    teachers = json.loads(os.environ["APROVAAI_LOCAL_TEACHERS"])
    if (engine.url.host not in {"localhost", "127.0.0.1", "::1"}
            or engine.url.database != "aprovaai" or len(password) < 16):
        raise RuntimeError("Seed exclusivo do PostgreSQL local aprovaai com senha de teste configurada")
    tokens = {}
    with SessionLocal.begin() as session:
        if session.scalar(text("SELECT current_schema()")) != "identity":
            raise RuntimeError("Seed de usuários exige schema identity")
        accounts = [("admin", "admin", "Admin Local"), ("aluno", "student", "Aluno Local"),
                    ("aluno-plano", "student", "Aluno Plano Completo")]
        accounts.extend((name, "teacher", display_name) for name, display_name in teachers.items())
        for name, role, display_name in accounts:
            email = f"{name}.local@exemplo.com"
            existing = session.scalar(select(User).where(User.email == email))
            if existing is not None:
                if existing.role != role or existing.status != "active":
                    raise RuntimeError(f"Conta existente divergente: {email}")
                user = existing
                profile = session.get(Profile, user.id)
                if name == "professor" and profile and profile.display_name == "Professor Local":
                    profile.display_name = display_name
            else:
                user = User(email=email, password_hash=hash_password(password), role=role,
                            status="active", is_active=True)
                session.add(user)
                session.flush()
                session.add(Profile(user_id=user.id, display_name=display_name, preferences={}))
            if "--tokens" in sys.argv and name != "admin":
                tokens[name] = SessionService().create(session, user, Settings.from_env()).access_token
    if "--tokens" in sys.argv:
        print(json.dumps(tokens))
    else:
        print("Contas locais criadas/preservadas pela identidade.")


if __name__ == "__main__":
    main()
