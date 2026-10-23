from alembic import context

from app.communication.models import Notification, Question
from app.database import Base, engine
from app.library_interaction.models import (
    ContentRating,
    LessonComment,
    LessonFavorite,
    LessonHistory,
    Playlist,
    PlaylistItem,
    PrivateNote,
)
from app.media.models import Media
from app.moderation.models import ContentReport, ModerationQueueItem

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=engine.url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
