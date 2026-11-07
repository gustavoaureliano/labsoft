from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LessonCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    course_id: str = Field(min_length=1, max_length=255)
    title: str = Field(min_length=1, max_length=255)
    description: str = ""
    position: int = Field(ge=1)


class LessonMediaUpdate(BaseModel):
    media_id: UUID | None


class LessonUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None


class LessonOrder(BaseModel):
    lesson_ids: list[str]


class LessonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    course_id: str
    title: str
    description: str
    position: int
    media_id: UUID | None
    thumbnail_id: UUID | None


class LessonPlaybackResponse(LessonResponse):
    media_id: UUID
    content_url: str
    duration_seconds: float | None = None
    position_seconds: float = 0
    completed: bool = False


class ProgressUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    position_seconds: float = Field(ge=0, allow_inf_nan=False)
    media_id: UUID


class ProgressResponse(BaseModel):
    position_seconds: float
    completed: bool
    updated_at: datetime | None = None
