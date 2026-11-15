"""Run Alembic migrations programmatically (used on application start-up)."""

from pathlib import Path

from alembic import command
from alembic.config import Config

ALEMBIC_DIR = Path(__file__).resolve().parents[3] / "alembic"


def upgrade_database(database_url: str) -> None:
    """Upgrade the database at ``database_url`` to the latest revision."""
    config = Config()
    config.set_main_option("script_location", str(ALEMBIC_DIR))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    command.upgrade(config, "head")
