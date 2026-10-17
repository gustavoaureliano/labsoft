import logging
from io import BytesIO
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import Annotated
from datetime import datetime

from app.database import get_session
from app.integrations import Integrations, User, get_current_user, get_integrations
from app.learning.dashboard import course_detail
from app.learning.models import Certificate
from app.learning.service import lock_course
from app.permissions import require_course

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/learning", tags=["Certificados"])


class CertificateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    verification_code: str
    course_id: str
    student_name: str
    course_title: str
    lesson_count: int
    workload_seconds: float
    issued_at: datetime


def issue_certificate(session: Session, user: User, integrations: Integrations, course_id: str) -> Certificate:
    if user.role != "student":
        raise HTTPException(403, "Certificado exclusivo do aluno")
    course = require_course(user, integrations, course_id)
    lock_course(session, course_id)
    certificate = session.scalar(select(Certificate).where(Certificate.student_id == user.id, Certificate.course_id == course_id))
    if certificate is None:
        detail = course_detail(session, user, course)
        if not detail["completed"]:
            raise HTTPException(409, "Conclua todas as aulas do curso antes de emitir")
        certificate = Certificate(student_id=user.id, course_id=course_id, student_name=user.name, course_title=course.title,
                                  lesson_count=detail["total_lessons"], workload_seconds=sum(lesson["duration_seconds"] or 0 for lesson in detail["lessons"]))
        session.add(certificate)
        session.commit()
    if not certificate.notification_sent:
        try:
            integrations.notify_certificate(user.id, str(certificate.id))
            certificate.notification_sent = True
            session.commit()
        except Exception:
            session.rollback()
            logger.warning("Certificate persisted, notification failed; retry on next issuance request", exc_info=True)
    return certificate


def owned_certificate(session: Session, user: User, certificate_id: UUID) -> Certificate:
    certificate = session.get(Certificate, certificate_id)
    if certificate is None:
        raise HTTPException(404, "Certificado não encontrado")
    if certificate.student_id != user.id:
        raise HTTPException(403, "Sem acesso ao certificado")
    return certificate


def certificate_pdf(certificate: Certificate) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)
    pdf.setTitle("Certificado de conclusão — AprovaAí")
    pdf.setFont("Helvetica-Bold", 26)
    pdf.drawCentredString(width / 2, height - 100, "AprovaAí — Certificado de conclusão")
    lines = [certificate.student_name, "concluiu o curso", certificate.course_title,
             f"{certificate.lesson_count} aulas · {certificate.workload_seconds / 60:.1f} minutos",
             f"Emitido em {certificate.issued_at:%d/%m/%Y}",
             f"Verificação: {certificate.verification_code}",
             "Emissão local de desenvolvimento — sem assinatura digital qualificada"]
    for index, line in enumerate(lines):
        size = 18 if index < 3 else 11
        while pdf.stringWidth(line, "Helvetica", size) > width - 80 and size > 7:
            size -= 1
        pdf.setFont("Helvetica", size)
        pdf.drawCentredString(width / 2, height - 160 - index * 38, line)
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


@router.post("/courses/{course_id}/certificate", response_model=CertificateResponse)
def issue(course_id: str, session: Annotated[Session, Depends(get_session)], user: Annotated[User, Depends(get_current_user)], integrations: Annotated[Integrations, Depends(get_integrations)]) -> CertificateResponse:
    return CertificateResponse.model_validate(issue_certificate(session, user, integrations, course_id))


@router.get("/certificates", response_model=list[CertificateResponse])
def list_certificates(session: Annotated[Session, Depends(get_session)], user: Annotated[User, Depends(get_current_user)]) -> list[CertificateResponse]:
    return [CertificateResponse.model_validate(item) for item in session.scalars(select(Certificate).where(Certificate.student_id == user.id).order_by(Certificate.issued_at.desc()))]


@router.get("/certificates/verify/{verification_code}")
def verify(verification_code: str, session: Annotated[Session, Depends(get_session)]) -> dict:
    certificate = session.scalar(select(Certificate).where(Certificate.verification_code == verification_code))
    if certificate is None:
        raise HTTPException(404, "Certificado não encontrado")
    return {"student_name": certificate.student_name, "course_title": certificate.course_title, "issued_at": certificate.issued_at, "verification_code": certificate.verification_code}


@router.get("/certificates/{certificate_id}", response_model=CertificateResponse)
def detail(certificate_id: UUID, session: Annotated[Session, Depends(get_session)], user: Annotated[User, Depends(get_current_user)]) -> CertificateResponse:
    return CertificateResponse.model_validate(owned_certificate(session, user, certificate_id))


@router.get("/certificates/{certificate_id}/download")
def download(certificate_id: UUID, session: Annotated[Session, Depends(get_session)], user: Annotated[User, Depends(get_current_user)]) -> Response:
    certificate = owned_certificate(session, user, certificate_id)
    return Response(certificate_pdf(certificate), media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="certificado-{certificate.id}.pdf"'})
