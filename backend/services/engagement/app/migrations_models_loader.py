"""Helper module to ensure all SQLAlchemy models are registered on Base.metadata."""

from app.communication.models import Notification, Question  # noqa: F401
from app.library_interaction.models import (  # noqa: F401
    ContentRating,
    LessonComment,
    LessonFavorite,
    LessonHistory,
    Playlist,
    PlaylistItem,
    PrivateNote,
)
from app.media.models import Media  # noqa: F401
from app.moderation.models import ContentReport, ModerationQueueItem  # noqa: F401
