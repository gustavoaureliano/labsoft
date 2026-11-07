import math
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.database import get_session
from app.integrations import principal, token
from .models import Course

router = APIRouter(prefix="/api", tags=["Course contracts"])


def summary(course):
    return {"id": str(course.id), "teacher_id": str(course.teacher_id), "teacher_name": course.teacher_name,
            "title": course.title, "status": course.status, "access_type": course.access_type,
            "price": str(course.price) if course.price is not None else None, "cover_url": None}


@router.get("/courses/{course_id}/summary")
def course_summary(course_id: UUID, request: Request, db: Session = Depends(get_session)):
    user = principal(request) if token(request, required=False) else None
    course = db.get(Course, course_id)
    if course is None or (course.status != "published" and not (user and user[1] == "teacher" and course.teacher_id == user[0])):
        raise HTTPException(404, "Curso não encontrado")
    return summary(course)


@router.get("/teacher/courses/summary")
def teacher_courses(request: Request, page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100), db: Session = Depends(get_session)):
    uid, role, _ = principal(request)
    if role != "teacher": raise HTTPException(403, "Ação exclusiva do professor")
    total = db.scalar(select(func.count()).select_from(Course).where(Course.teacher_id == uid))
    rows = db.scalars(select(Course).where(Course.teacher_id == uid).order_by(Course.updated_at.desc(), Course.id).offset((page-1)*size).limit(size))
    return {"items": [summary(c) for c in rows], "pagination": {"page": page, "size": size, "total": total, "pages": math.ceil(total/size)}}
