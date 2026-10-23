"""Tests for Alembic migration and explicit seed script."""

from pathlib import Path
import tempfile
import unittest

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from app.seed import seed_daniel_data


class TestMigrationsAndSeed(unittest.TestCase):
    def test_alembic_upgrade_downgrade_and_seed(self):
        backend_dir = Path(__file__).resolve().parent.parent
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_url = f"sqlite+pysqlite:///{Path(tmp_dir) / 'alembic_test.db'}"
            cfg = Config(str(backend_dir / "alembic.ini"))
            cfg.set_main_option("script_location", str(backend_dir / "migrations"))

            import app.database as db_module

            original_engine = db_module.engine
            test_engine = create_engine(db_url)
            db_module.engine = test_engine
            try:
                command.upgrade(cfg, "head")
                inspector = inspect(test_engine)
                tables = set(inspector.get_table_names())
                expected = {
                    "media",
                    "lesson_history",
                    "lesson_favorites",
                    "playlists",
                    "playlist_items",
                    "private_notes",
                    "lesson_comments",
                    "content_ratings",
                    "questions",
                    "notifications",
                    "content_reports",
                    "moderation_queue",
                }
                self.assertTrue(expected.issubset(tables))

                SessionTesting = sessionmaker(bind=test_engine)
                with SessionTesting() as session:
                    first_seed = seed_daniel_data(session)
                    self.assertEqual(first_seed["playlists"], 1)
                    self.assertEqual(first_seed["questions"], 3)
                    # Idempotent on second run
                    second_seed = seed_daniel_data(session)
                    self.assertEqual(second_seed["playlists"], 0)
                    self.assertEqual(second_seed["questions"], 0)

                command.downgrade(cfg, "45ac95d043fb")
                tables_after = set(inspect(test_engine).get_table_names())
                self.assertIn("media", tables_after)
                self.assertNotIn("playlists", tables_after)
            finally:
                db_module.engine = original_engine
                test_engine.dispose()

