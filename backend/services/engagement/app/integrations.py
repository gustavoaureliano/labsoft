"""Contracts for domains supplied by the other project members.

The development implementation is deliberately in memory, providing only what is
strictly required for Daniel's functionalities (F21-F26, F28-F32, F41, F43, F45).
Replace get_integrations when those modules are unified.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import os
from typing import Annotated, Any, Protocol

from fastapi import Depends, Header, HTTPException, Request


@dataclass(frozen=True)
class User:
    id: str
    role: str  # "student" | "teacher" | "admin"
    name: str


@dataclass(frozen=True)
class Course:
    id: str
    title: str
    owner_id: str
    teacher: str
    published: bool = True


@dataclass(frozen=True)
class LessonRef:
    id: str
    course_id: str
    title: str
    position: int
    duration_seconds: int = 900


@dataclass(frozen=True)
class AuditEntry:
    admin_id: str
    item_id: str
    item_type: str
    decision: str
    justification: str
    recorded_at: str


class Integrations(Protocol):
    def user(self, user_id: str) -> User | None: ...
    def course(self, course_id: str) -> Course | None: ...
    def courses(self) -> list[Course]: ...
    def lesson(self, lesson_id: str) -> LessonRef | None: ...
    def course_lessons(self, course_id: str) -> list[LessonRef]: ...
    def has_access(self, student_id: str, course_id: str) -> bool: ...
    def load_lesson_in_context(self, lesson_id: str, sequence: list[str]) -> dict[str, Any]: ...
    def course_engagement_snapshot(self, course_id: str, period: str) -> dict[str, Any]: ...
    def platform_snapshot(self, period: str) -> dict[str, Any]: ...
    def record_audit(
        self, admin_id: str, item_id: str, item_type: str, decision: str, justification: str
    ) -> AuditEntry: ...


@dataclass
class DemoIntegrations:
    users: dict[str, User] = field(
        default_factory=lambda: {
            "aluno-demo": User("aluno-demo", "student", "Bob Silva"),
            "aluno-demo-2": User("aluno-demo-2", "student", "Ana Souza"),
            "professor-demo": User("professor-demo", "teacher", "Prof. Fulano da Silva"),
            "professor-demo-2": User("professor-demo-2", "teacher", "Profa. Clara Mendonça"),
            "admin-demo": User("admin-demo", "admin", "Admin AprovaAí"),
        }
    )
    catalog: dict[str, Course] = field(
        default_factory=lambda: {
            "fisica-enem-mecanica": Course(
                "fisica-enem-mecanica",
                "Física para o ENEM: Mecânica",
                "professor-demo",
                "Prof. Fulano da Silva",
            ),
            "fisica-quantica": Course(
                "fisica-quantica",
                "Introdução à Física Quântica",
                "professor-demo",
                "Prof. Fulano da Silva",
            ),
            "biologia-celular": Course(
                "biologia-celular",
                "Biologia Celular",
                "professor-demo-2",
                "Profa. Clara Mendonça",
            ),
        }
    )
    lessons: dict[str, LessonRef] = field(
        default_factory=lambda: {
            "grandezas-vetores": LessonRef(
                "grandezas-vetores",
                "fisica-enem-mecanica",
                "Grandezas e vetores",
                1,
                1080,
            ),
            "movimento-uniforme": LessonRef(
                "movimento-uniforme",
                "fisica-enem-mecanica",
                "Movimento uniforme",
                2,
                1320,
            ),
            "movimento-variado": LessonRef(
                "movimento-variado",
                "fisica-enem-mecanica",
                "Movimento uniformemente variado",
                3,
                1560,
            ),
            "queda-livre": LessonRef(
                "queda-livre",
                "fisica-enem-mecanica",
                "Queda livre",
                4,
                1140,
            ),
            "lancamentos": LessonRef(
                "lancamentos",
                "fisica-enem-mecanica",
                "Lançamentos vertical e oblíquo",
                5,
                1680,
            ),
            "movimento-aceleracao": LessonRef(
                "movimento-aceleracao",
                "fisica-enem-mecanica",
                "Movimento e aceleração",
                6,
                1260,
            ),
            "introducao-forcas": LessonRef(
                "introducao-forcas",
                "fisica-enem-mecanica",
                "Introdução às forças",
                7,
                1200,
            ),
            "leis-newton": LessonRef(
                "leis-newton",
                "fisica-enem-mecanica",
                "Leis de Newton e suas aplicações",
                8,
                1440,
            ),
            "exercicios-dinamica": LessonRef(
                "exercicios-dinamica",
                "fisica-enem-mecanica",
                "Exercícios de dinâmica",
                9,
                1800,
            ),
            "trabalho-energia": LessonRef(
                "trabalho-energia",
                "fisica-enem-mecanica",
                "Trabalho e energia",
                10,
                1500,
            ),
            "impulso-quantidade": LessonRef(
                "impulso-quantidade",
                "fisica-enem-mecanica",
                "Impulso e quantidade de movimento",
                11,
                1380,
            ),
            "impulso-momento": LessonRef(
                "impulso-momento",
                "fisica-enem-mecanica",
                "Impulso e quantidade de movimento",
                11,
                1380,
            ),
            "revisao-mecanica": LessonRef(
                "revisao-mecanica",
                "fisica-enem-mecanica",
                "Revisão de mecânica",
                12,
                1920,
            ),
            "q1": LessonRef(
                "q1",
                "fisica-quantica",
                "Introdução e contexto histórico",
                1,
                1080,
            ),
            "q2": LessonRef(
                "q2",
                "fisica-quantica",
                "Radiação de corpo negro",
                2,
                1440,
            ),
            "q3": LessonRef(
                "q3",
                "fisica-quantica",
                "Efeito fotoelétrico",
                3,
                1260,
            ),
            "dualidade-onda-particula": LessonRef(
                "dualidade-onda-particula",
                "fisica-quantica",
                "Aula 02 — Dualidade Onda-Partícula",
                2,
                1140,
            ),
            "organelas-citoplasmaticas": LessonRef(
                "organelas-citoplasmaticas",
                "biologia-celular",
                "Aula 04 — Organelas Citoplasmáticas",
                1,
                900,
            ),
        }
    )
    grants: set[tuple[str, str]] = field(
        default_factory=lambda: {
            ("aluno-demo", "fisica-enem-mecanica"),
            ("aluno-demo", "fisica-quantica"),
            ("aluno-demo-2", "fisica-enem-mecanica"),
            ("aluno-demo-2", "biologia-celular"),
        }
    )
    audit_log: list[AuditEntry] = field(default_factory=list)

    def user(self, user_id: str) -> User | None:
        return self.users.get(user_id)

    def course(self, course_id: str) -> Course | None:
        return self.catalog.get(course_id)

    def courses(self) -> list[Course]:
        return list(self.catalog.values())

    def lesson(self, lesson_id: str) -> LessonRef | None:
        return self.lessons.get(lesson_id)

    def course_lessons(self, course_id: str) -> list[LessonRef]:
        items = [item for item in self.lessons.values() if item.course_id == course_id]
        return sorted(items, key=lambda item: item.position)

    def has_access(self, student_id: str, course_id: str) -> bool:
        return (student_id, course_id) in self.grants

    def load_lesson_in_context(self, lesson_id: str, sequence: list[str]) -> dict[str, Any]:
        """Mock for LessonPlaybackService.carregarAulaNoContexto(aulaId, sequencia) (F23)."""
        lesson_ref = self.lesson(lesson_id)
        if lesson_ref is None:
            raise KeyError("Aula não encontrada")
        idx = sequence.index(lesson_id)
        previous_id = sequence[idx - 1] if idx > 0 else None
        next_id = sequence[idx + 1] if idx + 1 < len(sequence) else None
        course = self.course(lesson_ref.course_id)
        return {
            "lesson_id": lesson_ref.id,
            "title": lesson_ref.title,
            "course_id": lesson_ref.course_id,
            "course_title": course.title if course else "",
            "duration_seconds": lesson_ref.duration_seconds,
            "previous_lesson_id": previous_id,
            "next_lesson_id": next_id,
            "sequence": sequence,
        }

    def course_engagement_snapshot(self, course_id: str, period: str) -> dict[str, Any]:
        """Mock for enrollment & progress metrics consumed by TeacherAnalyticsService (F41)."""
        multiplier = 1.0 if period == "30d" else (3.0 if period == "90d" else 12.0)
        base_by_course = {
            "fisica-enem-mecanica": {
                "enrollments": int(600 * multiplier),
                "active_students": 486,
                "completion_rate": 78.4,
                "avg_watch_minutes": 42,
            },
            "fisica-quantica": {
                "enrollments": int(92 * multiplier),
                "active_students": 74,
                "completion_rate": 81.2,
                "avg_watch_minutes": 38,
            },
            "biologia-celular": {
                "enrollments": int(210 * multiplier),
                "active_students": 165,
                "completion_rate": 75.0,
                "avg_watch_minutes": 40,
            },
        }
        return base_by_course.get(
            course_id,
            {
                "enrollments": 0,
                "active_students": 0,
                "completion_rate": 0.0,
                "avg_watch_minutes": 0,
            },
        )

    def platform_snapshot(self, period: str) -> dict[str, Any]:
        """Mock for general counts and access history consumed by AdminDashboardService (F43)."""
        access_series = (
            [
                {"label": "Semana 1", "count": 5460},
                {"label": "Semana 2", "count": 6320},
                {"label": "Semana 3", "count": 7180},
                {"label": "Semana 4", "count": 7560},
            ]
            if period == "monthly"
            else [
                {"label": "Jan", "count": 14200},
                {"label": "Fev", "count": 15800},
                {"label": "Mar", "count": 17300},
                {"label": "Abr", "count": 16900},
                {"label": "Mai", "count": 19100},
                {"label": "Jun", "count": 20700},
                {"label": "Jul", "count": 22400},
                {"label": "Ago", "count": 23100},
                {"label": "Set", "count": 26520},
                {"label": "Out", "count": 28100},
                {"label": "Nov", "count": 30200},
                {"label": "Dez", "count": 32700},
            ]
        )
        return {
            "total_users": 2516,
            "total_students": 2480,
            "total_teachers": 36,
            "total_courses": len(self.catalog),
            "access_series": access_series,
        }

    def record_audit(
        self, admin_id: str, item_id: str, item_type: str, decision: str, justification: str
    ) -> AuditEntry:
        """Mock for AuditService.registrarTrilhaAuditoria(adminId, itemId, decisao, justificativa) (F45)."""
        entry = AuditEntry(
            admin_id=admin_id,
            item_id=item_id,
            item_type=item_type,
            decision=decision,
            justification=justification,
            recorded_at=datetime.now(timezone.utc).isoformat(),
        )
        self.audit_log.append(entry)
        return entry


_DEFAULT_DEMO_INTEGRATIONS = DemoIntegrations()


def get_integrations() -> Integrations:
    if os.environ.get("LEARNING_DEMO_MODE", "false").lower() != "true":
        raise HTTPException(503, "Integrações reais ainda não configuradas")
    return _DEFAULT_DEMO_INTEGRATIONS


def get_current_user(
    request: Request,
    integrations: Annotated[Integrations, Depends(get_integrations)],
    x_demo_user: Annotated[str | None, Header(alias="X-Demo-User")] = None,
) -> User:
    role_to_user = {
        "student": "aluno-demo",
        "teacher": "professor-demo",
        "admin": "admin-demo",
    }
    role_cookie = (
        request.cookies.get("aprovaai_demo_role")
        or request.cookies.get("aprovaai-demo-role")
    )
    identity = (
        x_demo_user
        or request.headers.get("X-Demo-User")
        or request.cookies.get("aprovaai_demo_user")
        or (role_to_user.get(role_cookie or ""))
    )
    user = integrations.user(identity or "")
    if user is None:
        raise HTTPException(401, "Identifique o usuário de desenvolvimento")
    return user
