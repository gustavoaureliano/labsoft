"""Explicit development seed for Daniel's tables: python -m app.seed. Never runs on startup."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.communication.models import Notification, Question
from app.database import SessionLocal
from app.integrations import get_integrations
from app.library_interaction.models import (
    ContentRating,
    LessonComment,
    LessonFavorite,
    LessonHistory,
    Playlist,
    PlaylistItem,
    PrivateNote,
)
from app.moderation.models import ContentReport, ModerationQueueItem


def seed_daniel_data(session: Session) -> dict[str, int]:
    now = datetime.now(timezone.utc)
    created = {
        "playlists": 0,
        "favorites": 0,
        "history": 0,
        "notes": 0,
        "ratings": 0,
        "comments": 0,
        "questions": 0,
        "notifications": 0,
        "reports": 0,
    }

    if session.get(Playlist, "revisao-enem") is None:
        session.add(
            Playlist(
                id="revisao-enem",
                student_id="aluno-demo",
                name="Revisão ENEM",
            )
        )
        created["playlists"] += 1

    # Seed 5 ratings on q1 (4x 5 stars + 1x 4 stars = 4.8 average) so teacher analytics shows 4.8/5 from DB
    rating_fixtures = [
        ("rating-seed-1", "aluno-demo-2", "lesson", "q1", 5),
        ("rating-seed-2", "aluno-seed-3", "lesson", "q1", 5),
        ("rating-seed-3", "aluno-seed-4", "lesson", "q1", 5),
        ("rating-seed-4", "aluno-seed-5", "lesson", "q1", 5),
        ("rating-seed-5", "aluno-seed-6", "lesson", "q1", 4),
    ]
    for r_id, s_id, t_type, t_id, stars in rating_fixtures:
        if session.get(ContentRating, r_id) is None:
            session.add(
                ContentRating(
                    id=r_id,
                    student_id=s_id,
                    target_type=t_type,
                    target_id=t_id,
                    stars=stars,
                )
            )
            created["ratings"] += 1

    # Seed questions for student (aluno-demo) and teacher (professor-demo):
    # - 2 pending questions for professor-demo (Lucas Oliveira + Bob Silva)
    # - 1 answered question for professor-demo / aluno-demo (Bob Silva)
    question_fixtures = [
        Question(
            id="question-demo-lucas",
            student_id="aluno-lucas",
            student_name="Lucas Oliveira",
            course_id="fisica-quantica",
            lesson_id="q2",
            teacher_id="professor-demo",
            prompt="Professor, no efeito fotoelétrico, por que a energia cinética dos elétrons ejetados depende apenas da frequência da luz e não da intensidade?",
            status="pending",
            created_at=now - timedelta(minutes=15),
        ),
        Question(
            id="question-demo-1",
            student_id="aluno-demo",
            student_name="Bob Silva",
            course_id="fisica-enem-mecanica",
            lesson_id="leis-newton",
            teacher_id="professor-demo",
            prompt="Como identifico a força resultante quando o exercício mostra várias forças em sentidos diferentes?",
            status="answered",
            answer="Escolha um sentido positivo, some as forças nesse sentido e subtraia as forças no sentido contrário. O resultado com sinal indica o sentido da força resultante.",
            created_at=now - timedelta(hours=2),
            answered_at=now - timedelta(hours=1),
        ),
        Question(
            id="question-demo-2",
            student_id="aluno-demo",
            student_name="Bob Silva",
            course_id="fisica-enem-mecanica",
            lesson_id="trabalho-energia",
            teacher_id="professor-demo",
            prompt="Quando o trabalho de uma força deve ser considerado negativo?",
            status="pending",
            created_at=now - timedelta(days=1),
        ),
    ]
    for q in question_fixtures:
        if session.get(Question, q.id) is None:
            session.add(q)
            created["questions"] += 1

    notice_fixtures = [
        Notification(
            id="notice-demo-1",
            user_id="aluno-demo",
            kind="system",
            title="Continue sua aula de Física",
            description="Retome Leis de Newton e suas aplicações.",
            destination_url="/videoaula",
            is_read=False,
            created_at=now - timedelta(minutes=10),
        ),
        Notification(
            id="notice-demo-2",
            user_id="aluno-demo",
            kind="system",
            title="Sua dúvida pode ter uma resposta",
            description="Acompanhe suas discussões com os professores.",
            destination_url="/duvidas",
            is_read=False,
            created_at=now - timedelta(minutes=20),
        ),
        Notification(
            id="notice-demo-3",
            user_id="aluno-demo",
            kind="system",
            title="Revise seus cursos",
            description="Veja o andamento dos seus estudos.",
            destination_url="/meus-cursos",
            is_read=False,
            created_at=now - timedelta(minutes=30),
        ),
    ]
    for n in notice_fixtures:
        if session.get(Notification, n.id) is None:
            session.add(n)
            created["notifications"] += 1

    session.commit()
    return created


def reset_and_seed_daniel_data(session: Session) -> dict[str, int]:
    for model in (
        ModerationQueueItem,
        ContentReport,
        Notification,
        Question,
        ContentRating,
        LessonComment,
        PrivateNote,
        PlaylistItem,
        Playlist,
        LessonFavorite,
        LessonHistory,
    ):
        session.execute(delete(model))
    session.flush()
    return seed_daniel_data(session)


if __name__ == "__main__":
    get_integrations()  # Refuse to seed without explicit development mode (LEARNING_DEMO_MODE=true).
    with SessionLocal() as session:
        summary = seed_daniel_data(session)
        print(f"Seed concluído: {summary}; registros existentes preservados.")
