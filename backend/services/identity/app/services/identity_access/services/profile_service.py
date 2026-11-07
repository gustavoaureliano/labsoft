from __future__ import annotations

from sqlalchemy.orm import Session

from ..models import User, Profile
from ..schemas import ProfileUpdateIn
from .errors import ServiceError


class ProfileService:

    def create(
        self,
        db: Session,
        user: User,
        display_name: str,
    ) -> Profile:

        profile = Profile(
            user_id=user.id,
            display_name=display_name.strip(),
            preferences={},
        )

        db.add(profile)
        db.flush()

        return profile

    def get(
        self,
        db: Session,
        user: User,
    ) -> Profile:

        profile = db.get(
            Profile, user.id
        )

        if profile is None:
            raise ServiceError(
                "not_found",
                "Perfil não encontrado.",
            )

        return profile

    def update(
        self,
        db: Session,
        user: User,
        data: ProfileUpdateIn,
    ) -> Profile:

        profile = self.get(db, user)

        if data.display_name is not None:
            profile.display_name = (
                data.display_name.strip()
            )

        if data.preferences is not None:
            if len(data.preferences) > 30:
                raise ServiceError(
                    "invalid",
                    "Número excessivo de preferências.",
                )

            profile.preferences = data.preferences

        db.flush()

        return profile