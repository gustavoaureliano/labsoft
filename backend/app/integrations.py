"""Contracts for domains supplied by the other project members.

The development implementation is deliberately in memory, not a second course
or authentication backend. Replace get_integrations when those modules exist.
"""

import os
from dataclasses import dataclass
from typing import Protocol

from fastapi import Depends, HTTPException, Request


@dataclass(frozen=True)
class User:
    id: str
    role: str
    name: str


@dataclass(frozen=True)
class Course:
    id: str
    title: str
    owner_id: str
    image: str
    teacher: str
    published: bool = True


class Integrations(Protocol):
    def user(self, user_id: str) -> User | None: ...
    def course(self, course_id: str) -> Course | None: ...
    def courses(self) -> list[Course]: ...
    def has_access(self, student_id: str, course_id: str) -> bool: ...
    def recommendations(self, student_id: str) -> list[Course]: ...
    def notifications(self, user_id: str) -> list[dict[str, str]]: ...


class DemoIntegrations:
    users = {
        "aluno-demo": User("aluno-demo", "student", "Bob Silva"),
        "aluno-demo-2": User("aluno-demo-2", "student", "Ana Souza"),
        "professor-demo": User("professor-demo", "teacher", "Prof. Fulano da Silva"),
        "professor-demo-2": User("professor-demo-2", "teacher", "Profa. Clara Mendonça"),
    }
    catalog = {
        "fisica-quantica": Course(
            "fisica-quantica", "Introdução à Física Quântica", "professor-demo",
            "/images/courses/fisica-quantica.webp", "Prof. Fulano da Silva",
        ),
        "fisica-enem-mecanica": Course(
            "fisica-enem-mecanica", "Física para o ENEM: Mecânica", "professor-demo",
            "/images/courses/fisica-mecanica.webp", "Prof. Fulano da Silva",
        ),
        "biologia-celular": Course(
            "biologia-celular", "Biologia Celular", "professor-demo-2",
            "/images/courses/biologia-celular.webp", "Profa. Clara Mendonça",
        ),
    }
    grants = {
        ("aluno-demo", "fisica-quantica"),
        ("aluno-demo", "fisica-enem-mecanica"),
        ("aluno-demo-2", "fisica-enem-mecanica"),
    }

    def user(self, user_id: str) -> User | None:
        return self.users.get(user_id)

    def course(self, course_id: str) -> Course | None:
        return self.catalog.get(course_id)

    def courses(self) -> list[Course]:
        return list(self.catalog.values())

    def has_access(self, student_id: str, course_id: str) -> bool:
        return (student_id, course_id) in self.grants

    def recommendations(self, student_id: str) -> list[Course]:
        return []

    def notifications(self, user_id: str) -> list[dict[str, str]]:
        return []


def get_integrations() -> Integrations:
    if os.environ.get("LEARNING_DEMO_MODE", "false").lower() != "true":
        raise HTTPException(503, "Integrações reais ainda não configuradas")
    return DemoIntegrations()


def get_current_user(request: Request, integrations: Integrations = Depends(get_integrations)) -> User:
    # Explicitly insecure development identity; never enabled implicitly.
    identity = request.headers.get("X-Demo-User") or request.cookies.get("aprovaai_demo_user")
    user = integrations.user(identity or "")
    if user is None:
        raise HTTPException(401, "Identifique o usuário de desenvolvimento")
    return user
