"""Request and response schemas for ReportController and ContentModerationController."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ReportCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    item_id: str = Field(min_length=1, max_length=255)
    item_type: Literal["lesson", "course", "comment"]
    reason: str = Field(min_length=1, max_length=500)


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    reporter_id: str
    item_type: Literal["lesson", "course", "comment"]
    item_id: str
    reason: str
    status: Literal["pending", "resolved"]
    created_at: datetime


class ModerationQueueItemResponse(BaseModel):
    queue_id: str
    item_type: Literal["lesson", "course", "comment"]
    item_id: str
    title_or_excerpt: str
    author_or_owner: str
    reasons: list[str]
    reports_count: int
    status: Literal["pending", "kept", "hidden", "deleted"]
    created_at: datetime


class ModerationDecisionRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    item_type: Literal["lesson", "course", "comment"]
    decision: Literal["keep", "hide", "delete"]
    justification: str = Field(min_length=1, max_length=1000)


class ModerationDecisionResponse(BaseModel):
    queue_id: str
    item_type: Literal["lesson", "course", "comment"]
    item_id: str
    status: Literal["kept", "hidden", "deleted"]
    decision: Literal["keep", "hide", "delete"]
    admin_id: str
    justification: str
    decided_at: datetime
    audit_recorded: bool


class MyReportStatusResponse(BaseModel):
    reported: bool
    reason: str | None = None
    status: Literal["pending", "resolved"] | None = None
    decision: Literal["mantido", "ocultado", "excluído"] | None = None

