"""Request and response schemas for StudyLibraryController and LessonInteractionController."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class HistoryEntryResponse(BaseModel):
    lesson_id: str
    title: str
    course_id: str
    viewed_at: datetime


class FavoriteEntryResponse(BaseModel):
    lesson_id: str
    title: str
    course_id: str
    created_at: datetime


class PlaylistCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    name: str = Field(min_length=1, max_length=120)


class PlaylistRenameRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    name: str = Field(min_length=1, max_length=120)


class PlaylistLessonsUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    lesson_ids: list[str]


class PlaylistResponse(BaseModel):
    id: str
    name: str
    lesson_ids: list[str]
    created_at: datetime
    updated_at: datetime


class PlaylistPlaybackContextResponse(BaseModel):
    playlist_id: str
    playlist_name: str
    lesson_id: str
    title: str
    course_id: str
    course_title: str
    duration_seconds: int
    previous_lesson_id: str | None
    next_lesson_id: str | None
    sequence: list[str]


class PrivateNoteUpdateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    content: str = Field(min_length=1, max_length=5000)


class PrivateNoteResponse(BaseModel):
    student_id: str
    lesson_id: str
    content: str
    updated_at: datetime | None = None


class CommentCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    content: str = Field(min_length=1, max_length=2000)
    parent_id: str | None = None


class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    lesson_id: str
    author_id: str
    author_name: str
    parent_id: str | None
    content: str
    moderation_status: str
    created_at: datetime


class RatingUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target_type: Literal["lesson", "course"] = "lesson"
    stars: int = Field(ge=1, le=5)


class RatingSummaryResponse(BaseModel):
    target_type: Literal["lesson", "course"]
    target_id: str
    student_stars: int | None
    average_rating: float
    total_ratings: int
