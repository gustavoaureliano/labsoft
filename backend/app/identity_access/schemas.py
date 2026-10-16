from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)


class RegisterIn(BaseModel):
    email: EmailStr
    display_name: str = Field(
        min_length=2, max_length=120
    )
    password: str = Field(
        min_length=12, max_length=128
    )

    @field_validator("email")
    @classmethod
    def canonical_email(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        if (
            not any(c.isalpha() for c in value)
            or not any(c.isdigit() for c in value)
        ):
            raise ValueError(
                "A senha deve conter letras e números."
            )
        return value


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    role: Literal["student", "teacher", "admin"]


class TokenOut(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in_seconds: int
    user: UserOut


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    display_name: str
    preferences: dict
    avatar_url: str | None


class ProfileUpdateIn(BaseModel):
    display_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=120,
    )
    preferences: dict[
        str, str | int | float | bool | None
    ] | None = None


class PasswordRecoveryIn(BaseModel):
    email: EmailStr


class PasswordResetIn(BaseModel):
    token: str = Field(
        min_length=32, max_length=256
    )
    new_password: str = Field(
        min_length=12, max_length=128
    )

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        return RegisterIn.password_strength(value)


class TeacherApplicationIn(BaseModel):
    legal_name: str = Field(
        min_length=3, max_length=160
    )
    professional_summary: str = Field(
        min_length=20, max_length=4000
    )
    expertise: str = Field(
        min_length=3, max_length=240
    )
    document_ids: list[str] = Field(
        min_length=1, max_length=5
    )

    @field_validator("document_ids")
    @classmethod
    def unique_documents(
        cls, value: list[str]
    ) -> list[str]:
        if len(set(value)) != len(value):
            raise ValueError(
                "Os documentos não podem ser repetidos."
            )
        return value


class TeacherApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    legal_name: str
    professional_summary: str
    expertise: str
    status: Literal[
        "pending", "approved", "rejected"
    ]
    created_at: datetime
    document_ids: list[str]


class MediaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    original_name: str
    content_type: str
    size_bytes: int


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    category: str
    message: str
    details: dict
    created_at: datetime
    read_at: datetime | None


class StatusOut(BaseModel):
    message: str