"""Request and response schemas for TeacherAnalyticsController and AdminDashboardController."""

from typing import Literal

from pydantic import BaseModel


class MetricIndicator(BaseModel):
    value: float | int
    source: str
    description: str


class CourseAnalyticsItem(BaseModel):
    course_id: str
    course_title: str
    enrollments: int
    active_students: int
    completion_rate: float
    avg_watch_minutes: int
    average_rating: float
    total_ratings: int
    pending_questions: int
    answered_questions: int


class TeacherAnalyticsResponse(BaseModel):
    teacher_id: str
    period: Literal["30d", "90d", "365d"]
    course_id: str | None
    enrollments: MetricIndicator
    active_students: MetricIndicator
    completion_rate: MetricIndicator
    average_rating: MetricIndicator
    total_ratings: MetricIndicator
    question_response_rate: MetricIndicator
    courses: list[CourseAnalyticsItem]


class AccessSeriesPoint(BaseModel):
    label: str
    count: int


class AdminDashboardResponse(BaseModel):
    period: Literal["monthly", "annual"]
    total_users: int
    total_students: int
    total_teachers: int
    total_courses: int
    total_accesses_in_period: int
    pending_moderation_items: int
    held_comments_count: int
    access_series: list[AccessSeriesPoint]
