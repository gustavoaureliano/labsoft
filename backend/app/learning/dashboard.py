import logging
from dataclasses import asdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations import Course, Integrations, User
from app.learning.models import Lesson, LessonProgress
from app.learning.progress import get_progress
from app.learning.service import list_lessons
from app.media.models import Media
from app.media.storage import get_video_path

logger = logging.getLogger(__name__)


def lesson_summary(session: Session, lesson: Lesson, user: User, course: Course) -> dict:
    media = session.get(Media, lesson.media_id) if lesson.media_id else None
    playable = media is not None and media.status == "available"
    if playable:
        try:
            get_video_path(media.storage_key)
        except FileNotFoundError:
            playable = False
    progress = get_progress(session, user.id, lesson)
    thumbnail_url = f"/api/media/{lesson.thumbnail_id}/content" if lesson.thumbnail_id else course.image
    return {
        "id": lesson.id, "course_id": lesson.course_id, "title": lesson.title,
        "description": lesson.description, "position": lesson.position,
        "media_id": str(lesson.media_id) if lesson.media_id else None,
        "thumbnail_id": str(lesson.thumbnail_id) if lesson.thumbnail_id else None,
        "thumbnail_url": thumbnail_url, "duration_seconds": media.duration_seconds if media else None,
        "playable": playable, "position_seconds": progress.position_seconds,
        "completed": progress.completed,
    }


def course_detail(session: Session, user: User, course: Course) -> dict:
    lessons = [lesson_summary(session, lesson, user, course) for lesson in list_lessons(session, course.id)]
    completed = sum(lesson["completed"] for lesson in lessons)
    rows = list(session.scalars(select(LessonProgress).where(
        LessonProgress.student_id == user.id,
        LessonProgress.lesson_id.in_([lesson["id"] for lesson in lessons]),
    ).order_by(LessonProgress.updated_at.desc()))) if lessons else []
    by_id = {lesson["id"]: lesson for lesson in lessons}
    latest = next((by_id[row.lesson_id] for row in rows if by_id[row.lesson_id]["playable"] and str(row.media_id) == by_id[row.lesson_id]["media_id"]), None)
    continuation = latest if latest and not latest["completed"] else next(
        (lesson for lesson in lessons if lesson["playable"] and not lesson["completed"]),
        next((lesson for lesson in lessons if lesson["playable"]), None),
    )
    return {
        **asdict(course), "access_status": "active", "lessons": lessons,
        "sections": [{"title": "Aulas do curso", "lesson_ids": list(by_id)}],
        "completed_lessons": completed, "total_lessons": len(lessons),
        "progress": round(100 * completed / len(lessons)) if lessons else 0,
        "completed": bool(lessons) and completed == len(lessons),
        "continue_lesson": continuation,
        "last_studied_at": rows[0].updated_at if rows else None,
    }


def learning_courses(session: Session, user: User, integrations: Integrations) -> list[dict]:
    courses = []
    for course in integrations.courses():
        if user.role == "teacher" and course.owner_id == user.id:
            courses.append(course_detail(session, user, course))
        elif user.role == "student" and course.published:
            access = integrations.access_status(user.id, course.id)
            if access == "active":
                courses.append(course_detail(session, user, course))
            elif access in {"expired", "blocked"}:
                courses.append({
                    **asdict(course), "access_status": access, "lessons": [], "sections": [],
                    "total_lessons": 0, "completed_lessons": 0, "progress": 0,
                    "completed": False, "continue_lesson": None, "last_studied_at": None,
                })
    return courses


def dashboard(session: Session, user: User, integrations: Integrations) -> dict:
    courses = [course for course in learning_courses(session, user, integrations) if course["access_status"] == "active"]
    recent = sorted((course for course in courses if course["last_studied_at"] and course["continue_lesson"]), key=lambda c: c["last_studied_at"], reverse=True)
    current = recent[0] if recent else next((course for course in courses if course["continue_lesson"]), None)
    recommendations, notifications = [], []
    try:
        recommendations = [asdict(course) for course in integrations.recommendations(user.id) if course.published and course.id not in {item["id"] for item in courses}]
    except Exception:
        logger.warning("Recommendations unavailable", exc_info=True)
    try:
        notifications = integrations.notifications(user.id)
    except Exception:
        logger.warning("Notifications unavailable", exc_info=True)
    return {"courses": courses, "current_course": current, "recommendations": recommendations, "notifications": notifications}
