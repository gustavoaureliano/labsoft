"""Request and response schemas for the courses API."""

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class AccessType(StrEnum):
    FREE = "free"
    PAID = "paid"


class CourseStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class MaterialAccess(StrEnum):
    PUBLIC = "public"
    ENROLLED = "enrolled"


class CourseCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    subject: str = Field(min_length=2, max_length=120)
    area: str = Field(default="Geral", min_length=2, max_length=120)
    summary: str = Field(min_length=10, max_length=5000)
    exams: list[str] = Field(default_factory=list, max_length=30)
    access_type: AccessType
    price: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    cover_media_id: UUID | None = None


class CourseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    subject: str | None = Field(default=None, min_length=2, max_length=120)
    area: str | None = Field(default=None, min_length=2, max_length=120)
    summary: str | None = Field(default=None, min_length=10, max_length=5000)
    exams: list[str] | None = Field(default=None, max_length=30)
    access_type: AccessType | None = None
    price: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    cover_media_id: UUID | None = None


class LessonCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    summary: str = Field(default="", max_length=5000)
    duration_minutes: int = Field(default=0, ge=0, le=1440)
    position: int = Field(ge=0)
    video_media_id: UUID | None = None
    preview_available: bool = False


class LessonUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    summary: str | None = Field(default=None, max_length=5000)
    duration_minutes: int | None = Field(default=None, ge=0, le=1440)
    position: int | None = Field(default=None, ge=0)
    video_media_id: UUID | None = None
    preview_available: bool | None = None


class LessonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    course_id: UUID
    title: str
    summary: str
    duration_minutes: int
    position: int
    video_media_id: UUID | None
    preview_available: bool


class MaterialCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    description: str = Field(default="", max_length=5000)
    kind: str = Field(min_length=2, max_length=30)
    external_url: HttpUrl | None = None
    media_id: UUID | None = None
    lesson_id: UUID | None = None
    access_level: MaterialAccess = MaterialAccess.ENROLLED
    position: int = Field(default=0, ge=0)


class MaterialUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    kind: str | None = Field(default=None, min_length=2, max_length=30)
    external_url: HttpUrl | None = None
    lesson_id: UUID | None = None
    access_level: MaterialAccess | None = None
    position: int | None = Field(default=None, ge=0)


class MaterialResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    course_id: UUID
    lesson_id: UUID | None
    media_id: UUID | None
    title: str
    description: str
    kind: str
    external_url: str | None
    access_level: str
    position: int
    download_url: str | None = None
    authorized: bool = False


class CourseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    teacher_id: UUID
    teacher_name: str
    title: str
    subject: str
    area: str
    summary: str
    exams: list[str]
    access_type: str
    price: Decimal | None
    cover_media_id: UUID | None
    status: str
    featured: bool
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime


class CourseSummary(CourseResponse):
    lesson_count: int = 0
    student_count: int = 0
    rating: float | None = None


class Pagination(BaseModel):
    page: int
    size: int
    total: int
    pages: int


class CoursePage(BaseModel):
    items: list[CourseSummary]
    pagination: Pagination


class SearchResponse(BaseModel):
    courses: list[CourseSummary]
    materials: list[MaterialResponse]
    total: int


class AccessResponse(BaseModel):
    allowed: bool
    reason: str
    acquisition_required: bool


class CourseDetailsResponse(BaseModel):
    course: CourseSummary
    access: AccessResponse
    lessons: list[LessonResponse]
    reviews: list[dict]


class MaterialListResponse(BaseModel):
    course_id: UUID
    access: AccessResponse
    items: list[MaterialResponse]


class TeacherCourseSummary(CourseSummary):
    material_count: int = 0


class TeacherDashboardResponse(BaseModel):
    items: list[TeacherCourseSummary]
    total_courses: int
    published_courses: int
    draft_courses: int
    total_students: int


class LandingResponse(BaseModel):
    sample_courses: list[CourseSummary]
    featured_courses: list[CourseSummary]
    access_options: list[str]


class RecommendationResponse(BaseModel):
    items: list[CourseSummary]
    strategy: str


class CoursePreviewResponse(BaseModel):
    course: CourseResponse
    lessons: list[LessonResponse]
    materials: list[MaterialResponse]
    publication_pending: list[str]


class PublicationAction(StrEnum):
    PUBLISH = "publish"
    UNPUBLISH = "unpublish"


class PublicationRequest(BaseModel):
    action: PublicationAction


class PublicationResponse(BaseModel):
    course_id: UUID
    status: str
    published_at: datetime | None


class EnrollmentCreate(BaseModel):
    course_id: UUID
    student_id: UUID


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str = Field(default="", max_length=5000)
