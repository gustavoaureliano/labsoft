"""Request and response schemas for QuestionController and NotificationController."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class QuestionCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    course_id: str = Field(min_length=1, max_length=255)
    lesson_id: str | None = None
    prompt: str = Field(min_length=1, max_length=2000)


class QuestionAnswerRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    answer: str = Field(min_length=1, max_length=4000)


class QuestionResponse(BaseModel):
    id: str
    student_id: str
    student_name: str
    course_id: str
    course_title: str
    lesson_id: str | None
    lesson_title: str
    teacher_id: str
    teacher_name: str
    prompt: str
    status: Literal["pending", "answered"]
    answer: str | None
    created_at: datetime
    answered_at: datetime | None


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: str
    kind: str
    title: str
    description: str
    destination_url: str
    is_read: bool
    created_at: datetime


class NotificationReadResponse(BaseModel):
    id: str
    is_read: bool
    destination_url: str
