"""Engine and session factory creation."""

from __future__ import annotations

from typing import Any

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker


def create_db_engine(database_url: str) -> Engine:
    """Create an engine; SQLite gets foreign keys, WAL and thread-safe connections."""
    is_sqlite = database_url.startswith("sqlite")
    connect_args: dict[str, Any] = {"check_same_thread": False, "timeout": 15} if is_sqlite else {}
    engine = create_engine(database_url, connect_args=connect_args, pool_pre_ping=True)
    if is_sqlite:

        @event.listens_for(engine, "connect")
        def _sqlite_pragmas(dbapi_connection: Any, _record: Any) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()

    return engine


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Session factory; repositories open one short-lived session per operation."""
    return sessionmaker(bind=engine, expire_on_commit=False)
