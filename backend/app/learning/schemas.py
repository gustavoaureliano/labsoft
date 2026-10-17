from uuid import UUID

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
