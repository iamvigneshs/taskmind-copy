#!/usr/bin/env python
# Copyright (c) 2025 Acarin Inc. All rights reserved.
# Proprietary and confidential.
"""Initialize MissionMind TasksMind database with all tables."""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from sqlmodel import SQLModel, create_engine, text

# Import ALL models to ensure they're registered with SQLModel
from app.models import (
    Task, Assignment, User, OrgUnit, Authority,
    Comment, Attachment, Suspense, ExtensionRequest,
    RecordSeries, AuditLog,
    ClassificationLevel, TaskStatus, AssignmentRole,
    AssignmentState, CoordinationType, RiskLevel, EchelonLevel
)

# Load environment variables
load_dotenv()

def init_database():
    """Initialize database with all tables."""
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url or "sqlite" in database_url:
        print("❌ Error: PostgreSQL DATABASE_URL not found")
        print("Please set DATABASE_URL environment variable")
        return False
        
    print(f"Connecting to database...")
    print(f"Host: {database_url.split('@')[1].split(':')[0] if '@' in database_url else 'Unknown'}")
    print("-" * 70)
    
    try:
        # Create engine with appropriate settings
        if database_url.startswith("postgresql"):
            engine = create_engine(
                database_url,
                echo=False,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_pre_ping=True,
            )
        else:
            engine = create_engine(database_url, echo=False)
        
        # Test connection first
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✓ Database connection verified")
            
        # Drop all tables first (for clean slate)
        print("\nDropping existing tables...")
        SQLModel.metadata.drop_all(engine)
        print("✓ Existing tables dropped")
        
        # Create all tables
        print("\nCreating database tables...")
        SQLModel.metadata.create_all(engine)
        print("✓ All tables created successfully")
        
        # Verify tables were created
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            
            print(f"\n✓ Created {len(tables)} tables:")
            for table in tables:
                # Get column count
                col_result = conn.execute(text(f"""
                    SELECT COUNT(*) 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = '{table}'
                """))
                col_count = col_result.fetchone()[0]
                print(f"  - {table} ({col_count} columns)")
        
        print("-" * 70)
        print("✅ Database initialization completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error during database initialization:")
        print(f"   {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)