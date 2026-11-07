import logging
from io import BytesIO
from html import escape
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
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
    primary = colors.HexColor("#075A76")
    ink = colors.HexColor("#20343C")
    muted = colors.HexColor("#536D79")
    pdf.setFillColor(colors.HexColor("#F5F8FA"))
    pdf.rect(0, 0, width, height, stroke=0, fill=1)
    pdf.setStrokeColor(colors.HexColor("#BDD4DE"))
    pdf.roundRect(24, 24, width - 48, height - 48, 9, stroke=1, fill=0)

    pdf.setFillColor(primary)
    pdf.roundRect(24, height - 146, width - 48, 122, 9, stroke=0, fill=1)
    pdf.rect(24, height - 146, width - 48, 14, stroke=0, fill=1)
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(48, height - 62, "AprovaAí")
    pdf.setFont("Helvetica", 10)
    pdf.drawRightString(width - 48, height - 60, "EMISSÃO LOCAL DE DESENVOLVIMENTO")
    pdf.setFont("Helvetica-Bold", 27)
    pdf.drawCentredString(width / 2, height - 119, "Certificado de conclusão")

    def centered_text(value: str, top: float, max_height: float, start_size: int, color: colors.Color) -> None:
        available_width = width - 110
        for size in range(start_size, 9, -1):
            style = ParagraphStyle("certificate-text", fontName="Helvetica-Bold", fontSize=size,
                                   leading=size * 1.18, alignment=TA_CENTER, textColor=color)
            paragraph = Paragraph(escape(value), style)
            _, paragraph_height = paragraph.wrap(available_width, max_height)
            if paragraph_height <= max_height or size == 10:
                paragraph.drawOn(pdf, 55, top - paragraph_height)
                return

    pdf.setFillColor(muted)
    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(width / 2, height - 173, "Registramos que")
    centered_text(certificate.student_name, height - 182, 52, 24, ink)
    pdf.setFillColor(muted)
    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(width / 2, height - 260, "concluiu o curso")
    centered_text(certificate.course_title, height - 269, 52, 21, primary)

    total_seconds = round(certificate.workload_seconds)
    hours, remaining = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remaining, 60)
    duration = f"{hours} h {minutes} min" if hours else f"{minutes} min"
    if seconds:
        duration += f" {seconds} s"
    details = (
        ("AULAS NA EMISSÃO", str(certificate.lesson_count)),
        ("DURAÇÃO DOS VÍDEOS", duration),
        ("EMITIDO EM", f"{certificate.issued_at:%d/%m/%Y}"),
    )
    card_width = (width - 120) / 3
    for index, (label, value) in enumerate(details):
        x = 48 + index * (card_width + 12)
        pdf.setFillColor(colors.white)
        pdf.setStrokeColor(colors.HexColor("#D5E3E9"))
        pdf.roundRect(x, 150, card_width, 67, 6, stroke=1, fill=1)
        pdf.setFillColor(muted)
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(x + 14, 192, label)
        pdf.setFillColor(ink)
        pdf.setFont("Helvetica-Bold", 15)
        pdf.drawString(x + 14, 168, value)

    pdf.setFillColor(muted)
    pdf.setFont("Helvetica", 10)
    pdf.drawCentredString(width / 2, 119, "Código de verificação")
    pdf.setFillColor(primary)
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawCentredString(width / 2, 101, certificate.verification_code)
    pdf.setFillColor(muted)
    pdf.setFont("Helvetica", 9)
    pdf.drawCentredString(width / 2, 67, "Este registro é de desenvolvimento e não constitui assinatura digital qualificada.")
    pdf.drawCentredString(width / 2, 53, "A duração representa os vídeos do curso na emissão, não horas assistidas.")
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
    return Response(certificate_pdf(certificate), media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="certificado-{certificate.id}.pdf"', "Cache-Control": "private, no-store"})
