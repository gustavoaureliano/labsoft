import math
import os
import secrets
from uuid import UUID
from typing import Literal
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.database import get_session
from app.integrations import principal, token
from .models import Course

router = APIRouter(prefix="/api", tags=["Course contracts"])


class ModerationIn(BaseModel):
    decision: Literal["keep", "hide", "delete"]


def summary(course):
    return {"id": str(course.id), "teacher_id": str(course.teacher_id), "teacher_name": course.teacher_name,
            "title": course.title, "status": course.status, "access_type": course.access_type,
            "price": str(course.price) if course.price is not None else None, "cover_url": course.cover_url,
            "moderation_status": course.moderation_status}


@router.get("/courses/{course_id}/summary")
def course_summary(course_id: UUID, request: Request, db: Session = Depends(get_session)):
    user = principal(request) if token(request, required=False) else None
    course = db.get(Course, course_id)
    owner = user and course is not None and (user[1] == "admin" or user[1] == "teacher" and course.teacher_id == user[0])
    if course is None or not owner and (course.status != "published" or course.moderation_status != "visible"):
        raise HTTPException(404, "Curso não encontrado")
    return summary(course)


@router.get("/teacher/courses/summary")
def teacher_courses(request: Request, page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100), db: Session = Depends(get_session)):
    uid, role, _ = principal(request)
    if role != "teacher": raise HTTPException(403, "Ação exclusiva do professor")
    total = db.scalar(select(func.count()).select_from(Course).where(Course.teacher_id == uid))
    rows = db.scalars(select(Course).where(Course.teacher_id == uid).order_by(Course.updated_at.desc(), Course.id).offset((page-1)*size).limit(size))
    return {"items": [summary(c) for c in rows], "pagination": {"page": page, "size": size, "total": total, "pages": math.ceil(total/size)}}


@router.put("/courses/{course_id}/moderation")
def moderate_course(course_id: UUID, body: ModerationIn, request: Request,
                    service_token: str | None = Header(default=None, alias="X-Service-Token"),
                    db: Session = Depends(get_session)):
    expected = os.getenv("INTERNAL_SERVICE_TOKEN", "")
    if len(expected) < 16 or not service_token or not secrets.compare_digest(service_token, expected):
        raise HTTPException(403, "Comando exclusivo do serviço de moderação")
    _, role, _ = principal(request)
    if role != "admin":
        raise HTTPException(403, "Ação exclusiva do administrador")
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(404, "Curso não encontrado")
    if course.moderation_status == "deleted" and body.decision != "delete":
        raise HTTPException(409, "Exclusão lógica não pode ser revertida")
    course.moderation_status = {"keep":"visible", "hide":"hidden", "delete":"deleted"}[body.decision]
    db.commit()
    return {"course_id": str(course_id), "moderation_status": course.moderation_status}
