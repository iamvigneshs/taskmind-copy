# Copyright (c) 2025 Acarin Inc. All rights reserved.
# Proprietary and confidential.
"""Clean database configuration for MissionMind - Multi-tenant support."""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator
from dotenv import load_dotenv

from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy import text

# Load environment variables from .env file
load_dotenv()

# SAFETY: Ensure we're using PostgreSQL RDS, not SQLite
# DATABASE_URL = os.getenv("DATABASE_URL")

DATABASE_URL= "postgresql://AN24_Acabot:lAyWkB5FIXghQpvNYM5ggpITC@acabot-dbcluster-dev.cluster-cp2eea8yihxz.us-east-1.rds.amazonaws.com:5432/taskmind"
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in environment. Please check .env file")
if not DATABASE_URL.startswith("postgresql://"):
    raise ValueError("SAFETY: Only PostgreSQL RDS database is allowed. SQLite is forbidden.")

# Database connection pool settings
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))
DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))

# Configure PostgreSQL connection with pooling
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_size=DB_POOL_SIZE,
    max_overflow=DB_MAX_OVERFLOW,
    pool_timeout=DB_POOL_TIMEOUT,
    pool_pre_ping=True,  # Verify connections before use
)


def init_db() -> None:
    """Create database tables for multi-tenant models."""
    # Import all models to ensure they're registered with SQLModel metadata
    from app.models import Tenant, User, OrgUnit
    # from app.models_templates import (
    #     OrgLevelTemplate, ApprovalTemplate, AuthorityPosition
    # )  # Temporarily disabled for simplified setup
    
    print("🗄️  Creating database tables for MissionMind...")
    
    # Try to drop existing tables with CASCADE for clean schema recreation
    try:
        print("⚠️  Dropping existing tables to recreate with new schema...")
        with engine.connect() as conn:
            # Drop all tables with CASCADE to handle foreign key constraints
            conn.execute(text("DROP SCHEMA public CASCADE"))
            conn.execute(text("CREATE SCHEMA public"))
            conn.execute(text("GRANT ALL ON SCHEMA public TO postgres"))
            conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
            conn.commit()
        print("✅ Schema dropped and recreated")
    except Exception as e:
        print(f"ℹ️  Schema reset not needed or failed: {e}")
    
    # Create all tables
    SQLModel.metadata.create_all(engine)
    print("✅ Database tables created successfully")


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


def check_database_connection() -> bool:
    """Test database connectivity."""
    try:
        with Session(engine) as session:
            session.exec("SELECT 1").first()
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def reset_database() -> None:
    """DANGER: Drop all tables and recreate. Use only in development."""
    import sys
    
    if os.getenv("ENVIRONMENT") == "production":
        print("❌ SAFETY: Cannot reset database in production")
        return
    
    print("⚠️  WARNING: This will drop all database tables!")
    confirm = input("Type 'RESET DATABASE' to continue: ")
    if confirm != "RESET DATABASE":
        print("❌ Database reset cancelled")
        return
    
    # Drop all tables
    print("🗑️  Dropping all tables...")
    SQLModel.metadata.drop_all(engine)
    print("✅ All tables dropped")
    
    # Recreate tables
    init_db()
    print("✅ Database reset complete")


if __name__ == "__main__":
    """Script to initialize or reset database."""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "reset":
        reset_database()
    else:
        if check_database_connection():
            init_db()
        else:
            print("❌ Cannot initialize database - connection failed")
