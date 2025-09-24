# Copyright (c) 2025 Acarin Inc. All rights reserved.
# Proprietary and confidential.
"""Database configuration for MissionMind MVP service layer."""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

from sqlmodel import Session, SQLModel, create_engine

DEFAULT_DB_URL = "sqlite:///./missionmind.db"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DB_URL)

# Database connection pool settings
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))
DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))

# Configure connection arguments based on database type
if DATABASE_URL.startswith("sqlite"):
    # SQLite-specific settings for FastAPI async
    connect_args = {"check_same_thread": False}
    engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)
elif DATABASE_URL.startswith("postgresql"):
    # PostgreSQL with connection pooling
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        pool_size=DB_POOL_SIZE,
        max_overflow=DB_MAX_OVERFLOW,
        pool_timeout=DB_POOL_TIMEOUT,
        pool_pre_ping=True,  # Verify connections before use
    )
else:
    # Default for other databases
    engine = create_engine(DATABASE_URL, echo=False)


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
