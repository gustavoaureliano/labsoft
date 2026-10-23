"""HTTP routes for the catalog and course-management responsibilities."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Query, Response, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_session
from app.media.models import Media
from app.media.storage import LocalMediaStorage

from .exceptions import MediaNotFound
from .repository import CourseRepository
from .schemas import (
    CourseCreate,
    CourseDetailsResponse,
    CoursePage,
    CoursePreviewResponse,
    CourseResponse,
    CourseUpdate,
    LandingResponse,
    LessonCreate,
    LessonResponse,
    LessonUpdate,
    MaterialCreate,
    MaterialListResponse,
    MaterialResponse,
    MaterialUpdate,
    PublicationRequest,
    PublicationResponse,
    RecommendationResponse,
    SearchResponse,
    TeacherDashboardResponse,
)
from .service import (
    CatalogService,
    CourseService,
    MaterialService,
    PublishingService,
    RecommendationService,
    TeacherCourseService,
)


router = APIRouter(prefix="/api", tags=["courses"])

SessionDependency = Annotated[Session, Depends(get_session)]


def teacher_context(
    teacher_id: Annotated[UUID, Header(alias="X-Teacher-Id")],
    teacher_name: Annotated[str, Header(alias="X-Teacher-Name")] = "Professor",
) -> tuple[UUID, str]:
    return teacher_id, teacher_name


TeacherDependency = Annotated[tuple[UUID, str], Depends(teacher_context)]


@router.get("/landing", response_model=LandingResponse)
def landing(session: SessionDependency) -> LandingResponse:
    return CatalogService(session).landing()


@router.get("/search", response_model=SearchResponse)
def search(
    session: SessionDependency,
    q: Annotated[str, Query(min_length=2, max_length=200)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> SearchResponse:
    return CatalogService(session).search(q, limit=limit)


@router.get("/recommendations", response_model=RecommendationResponse)
def recommendations(
    session: SessionDependency,
    student_id: Annotated[UUID, Header(alias="X-Student-Id")],
    limit: Annotated[int, Query(ge=1, le=50)] = 6,
) -> RecommendationResponse:
    return RecommendationService(session).recommend(student_id, limit=limit)


@router.get("/teacher/courses", response_model=TeacherDashboardResponse)
def teacher_courses(
    session: SessionDependency, teacher: TeacherDependency
) -> TeacherDashboardResponse:
    teacher_id, _ = teacher
    return TeacherCourseService(session).dashboard(teacher_id)


@router.get("/courses", response_model=CoursePage)
def explore_courses(
    session: SessionDependency,
    subject: str | None = None,
    area: str | None = None,
    exam: str | None = None,
    access_type: Annotated[str | None, Query(pattern="^(free|paid)$")] = None,
    order: Annotated[
        str, Query(pattern="^(relevance|rating|popular|newest|title)$")
    ] = "relevance",
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> CoursePage:
    return CatalogService(session).list_courses(
        subject=subject,
        area=area,
        exam=exam,
        access_type=access_type,
        order=order,
        page=page,
        size=size,
    )


@router.post("/courses", response_model=CourseResponse, status_code=201)
def create_course(
    payload: CourseCreate,
    session: SessionDependency,
    teacher: TeacherDependency,
) -> CourseResponse:
    teacher_id, teacher_name = teacher
    return CourseService(session).create(
        payload, teacher_id=teacher_id, teacher_name=teacher_name
    )


@router.get("/courses/{course_id}", response_model=CourseDetailsResponse)
def course_details(
    course_id: UUID,
    session: SessionDependency,
    student_id: Annotated[UUID | None, Header(alias="X-Student-Id")] = None,
) -> CourseDetailsResponse:
    return CatalogService(session).details(course_id, student_id=student_id)


@router.patch("/courses/{course_id}", response_model=CourseResponse)
def update_course(
    course_id: UUID,
    payload: CourseUpdate,
    session: SessionDependency,
    teacher: TeacherDependency,
) -> CourseResponse:
    teacher_id, _ = teacher
    return CourseService(session).update(course_id, payload, teacher_id=teacher_id)


@router.post("/courses/{course_id}/lessons", response_model=LessonResponse, status_code=201)
def create_lesson(
    course_id: UUID,
    payload: LessonCreate,
    session: SessionDependency,
    teacher: TeacherDependency,
) -> LessonResponse:
    teacher_id, _ = teacher
    return CourseService(session).add_lesson(course_id, payload, teacher_id=teacher_id)


@router.patch("/courses/{course_id}/lessons/{lesson_id}", response_model=LessonResponse)
def update_lesson(
    course_id: UUID,
    lesson_id: UUID,
    payload: LessonUpdate,
    session: SessionDependency,
    teacher: TeacherDependency,
) -> LessonResponse:
    teacher_id, _ = teacher
    return CourseService(session).update_lesson(
        course_id, lesson_id, payload, teacher_id=teacher_id
    )


@router.delete("/courses/{course_id}/lessons/{lesson_id}", status_code=204)
def delete_lesson(
    course_id: UUID,
    lesson_id: UUID,
    session: SessionDependency,
    teacher: TeacherDependency,
) -> Response:
    teacher_id, _ = teacher
    CourseService(session).delete_lesson(course_id, lesson_id, teacher_id=teacher_id)
    return Response(status_code=204)


@router.get("/courses/{course_id}/materials", response_model=MaterialListResponse)
def course_materials(
    course_id: UUID,
    session: SessionDependency,
    lesson_id: UUID | None = None,
    student_id: Annotated[UUID | None, Header(alias="X-Student-Id")] = None,
) -> MaterialListResponse:
    storage = LocalMediaStorage()
    return MaterialService(session).list_authorized(
        course_id,
        student_id=student_id,
        lesson_id=lesson_id,
        download_url_factory=storage.signed_url,
    )


@router.post("/courses/{course_id}/materials", response_model=MaterialResponse, status_code=201)
def create_material(
    course_id: UUID,
    payload: MaterialCreate,
    session: SessionDependency,
    teacher: TeacherDependency,
) -> MaterialResponse:
    teacher_id, _ = teacher
    return MaterialService(session).create(course_id, payload, teacher_id=teacher_id)


@router.post(
    "/courses/{course_id}/materials/upload",
    response_model=MaterialResponse,
    status_code=201,
)
def upload_material(
    course_id: UUID,
    session: SessionDependency,
    teacher: TeacherDependency,
    file: Annotated[UploadFile, File()],
    title: Annotated[str, Form(min_length=2, max_length=200)],
    kind: Annotated[str, Form(min_length=2, max_length=30)],
    description: Annotated[str, Form()] = "",
    access_level: Annotated[str, Form(pattern="^(public|enrolled)$")] = "enrolled",
    position: Annotated[int, Form(ge=0)] = 0,
    lesson_id: Annotated[UUID | None, Form()] = None,
) -> MaterialResponse:
    teacher_id, _ = teacher
    storage = LocalMediaStorage()
    storage_key = None
    try:
        storage_key, size = storage.save(file)
        media = Media(
            storage_key=storage_key,
            original_filename=file.filename or "file",
            content_type=file.content_type or "application/octet-stream",
            size_bytes=size,
            status="available",
        )
        return MaterialService(session).create_from_upload(
            course_id,
            media=media,
            title=title,
            description=description,
            kind=kind,
            access_level=access_level,
            position=position,
            lesson_id=lesson_id,
            teacher_id=teacher_id,
        )
    except ValueError as error:
        raise HTTPException(status_code=413, detail=str(error)) from error
    except Exception:
        if storage_key:
            storage.delete(storage_key)
        raise


@router.patch(
    "/courses/{course_id}/materials/{material_id}", response_model=MaterialResponse
)
def update_material(
    course_id: UUID,
    material_id: UUID,
    payload: MaterialUpdate,
    session: SessionDependency,
    teacher: TeacherDependency,
) -> MaterialResponse:
    teacher_id, _ = teacher
    return MaterialService(session).update(
        course_id, material_id, payload, teacher_id=teacher_id
    )


@router.delete("/courses/{course_id}/materials/{material_id}", status_code=204)
def delete_material(
    course_id: UUID,
    material_id: UUID,
    session: SessionDependency,
    teacher: TeacherDependency,
) -> Response:
    teacher_id, _ = teacher
    media = MaterialService(session).delete(
        course_id, material_id, teacher_id=teacher_id
    )
    if media:
        LocalMediaStorage().delete(media.storage_key)
    return Response(status_code=204)


@router.get("/courses/{course_id}/preview", response_model=CoursePreviewResponse)
def preview_course(
    course_id: UUID,
    session: SessionDependency,
    teacher: TeacherDependency,
) -> CoursePreviewResponse:
    teacher_id, _ = teacher
    return PublishingService(session).preview(course_id, teacher_id=teacher_id)


@router.post("/courses/{course_id}/publication", response_model=PublicationResponse)
def set_course_publication(
    course_id: UUID,
    payload: PublicationRequest,
    session: SessionDependency,
    teacher: TeacherDependency,
) -> PublicationResponse:
    teacher_id, _ = teacher
    return PublishingService(session).set_publication(
        course_id, action=payload.action.value, teacher_id=teacher_id
    )


@router.get("/media/{media_id}/download")
def download_media(
    media_id: UUID,
    expires: int,
    signature: str,
    session: SessionDependency,
) -> FileResponse:
    storage = LocalMediaStorage()
    if not storage.validate(media_id, expires, signature):
        raise HTTPException(status_code=403, detail="Link expirado ou inválido.")
    media = CourseRepository(session).get_media(media_id)
    if not media or media.status != "available":
        raise MediaNotFound("Mídia não encontrada ou indisponível.")
    path = storage.path(media.storage_key)
    if not path.is_file():
        raise MediaNotFound("Arquivo não encontrado no armazenamento.")
    return FileResponse(
        path,
        media_type=media.content_type,
        filename=media.original_filename,
    )
