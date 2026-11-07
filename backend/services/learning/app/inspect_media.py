"""Inspect one existing video explicitly, preserving its file and associations."""

import argparse
from uuid import UUID

from app.database import SessionLocal
from app.media.inspection import inspect_video
from app.media.models import Media
from app.media.storage import get_video_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("media_id", type=UUID)
    args = parser.parse_args()
    with SessionLocal() as session:
        media = session.get(Media, args.media_id)
        if media is None:
            parser.error("Mídia inexistente")
        info = inspect_video(get_video_path(media.storage_key), media.content_type)
        media.duration_seconds = info.duration_seconds
        media.codec = info.codec
        session.commit()
        print(f"Duração: {info.duration_seconds}s; codec: {info.codec}. Arquivo preservado.")
