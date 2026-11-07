"""NotificationService implementation (F32, plus triggers from F25, F29, F31)."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.communication.models import Notification


class NotificationNotFound(Exception):
    pass


def obter_avisos_do_usuario(session: Session, user_id: str) -> list[Notification]:
    """F32 — Consultar notificações ordenadas por data decrescente."""
    return list(
        session.scalars(
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc(), Notification.id.desc())
        )
    )


def confirmar_leitura(
    session: Session, user_id: str, notification_id: str
) -> Notification:
    """F32 — Atualizar estado do aviso para LIDO e retornar estado atualizado e link de destino."""
    notification = session.get(Notification, notification_id)
    if notification is None or notification.user_id != user_id:
        raise NotificationNotFound("Notificação não encontrada")
    notification.is_read = True
    session.commit()
    session.refresh(notification)
    return notification


def notificar_autor_original(
    session: Session, parent_author_id: str, lesson_id: str, reply_author_name: str
) -> Notification:
    """F25 — Registrar notificação de nova resposta a comentário."""
    notification = Notification(
        user_id=parent_author_id,
        kind="comment_reply",
        title="Nova resposta ao seu comentário",
        description=f"{reply_author_name} respondeu ao seu comentário na aula.",
        destination_url=f"/videoaula?aula={lesson_id}",
        is_read=False,
    )
    session.add(notification)
    session.flush()
    return notification


def notificar_professor(
    session: Session, teacher_id: str, question_id: str, course_title: str
) -> Notification:
    """F29 — Criar notificação de nova dúvida para o professor responsável."""
    notification = Notification(
        user_id=teacher_id,
        kind="new_question",
        title="Nova dúvida recebida",
        description=f"Um aluno enviou uma nova dúvida em {course_title}.",
        destination_url=f"/professor/duvidas?duvida={question_id}",
        is_read=False,
    )
    session.add(notification)
    session.flush()
    return notification


def notificar_aluno(
    session: Session, student_id: str, question_id: str, course_title: str
) -> Notification:
    """F31 — Criar aviso de dúvida respondida para o aluno."""
    notification = Notification(
        user_id=student_id,
        kind="question_answered",
        title="Sua dúvida foi respondida",
        description=f"O professor respondeu sua dúvida no curso {course_title}.",
        destination_url=f"/duvidas?duvida={question_id}",
        is_read=False,
    )
    session.add(notification)
    session.flush()
    return notification
