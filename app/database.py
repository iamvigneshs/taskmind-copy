"""Database configuration for MissionMind MVP service layer."""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

from sqlmodel import Session, SQLModel, create_engine

DEFAULT_DB_URL = "sqlite:///./missionmind.db"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DB_URL)

# For SQLite we need check_same_thread=False when using FastAPI async dependencies.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)


def init_db() -> None:
    """Create database tables. Call during startup or seeding."""
    SQLModel.metadata.create_all(engine)


@contextmanager
def session_scope() -> Iterator[Session]:
    """Provide a transactional scope for scripts."""
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_session() -> Iterator[Session]:
    """FastAPI dependency that yields a scoped session."""
    with Session(engine) as session:
        yield session
