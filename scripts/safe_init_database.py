#!/usr/bin/env python3
# Copyright (c) 2025 Acarin Inc. All rights reserved.
# Proprietary and confidential.
"""SAFE database initialization with protection against accidental data loss."""
from __future__ import annotations

import sys
from datetime import datetime
from sqlmodel import Session, select, text

from app.database import engine, init_db
from app.models import Task, OrgUnit, Authority


def check_existing_data(session: Session) -> dict:
    """Check if tables exist and contain data."""
    results = {
        "tables_exist": False,
        "has_data": False,
        "counts": {}
    }
    
    try:
        # Check if tables exist
        result = session.exec(text("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('task', 'orgunit', 'authority', 'assignment', 'user')
        """))
        table_count = result.one()[0]
        results["tables_exist"] = table_count > 0
        
        if results["tables_exist"]:
            # Count records in main tables
            for model, table_name in [(Task, 'task'), (OrgUnit, 'orgunit'), (Authority, 'authority')]:
                try:
                    count = session.query(model).count()
                    results["counts"][table_name] = count
                    if count > 0:
                        results["has_data"] = True
                except:
                    results["counts"][table_name] = 0
    except Exception as e:
        print(f"Error checking existing data: {e}")
    
    return results


def safe_init_database():
    """Initialize database with safety checks."""
    print("🛡️  MissionMind Safe Database Initialization")
    print("=" * 50)
    
    # Create a session to check existing data
    with Session(engine) as session:
        existing_data = check_existing_data(session)
        
        if existing_data["tables_exist"]:
            print("\n⚠️  WARNING: Database tables already exist!")
            print(f"Current data counts:")
            for table, count in existing_data["counts"].items():
                print(f"  - {table}: {count} records")
            
            if existing_data["has_data"]:
                print("\n🚨 CRITICAL: Database contains existing data!")
                print("Creating tables would potentially cause data loss.")
                print("\nOptions:")
                print("1. Exit without changes (recommended)")
                print("2. Continue anyway (DANGEROUS - requires explicit confirmation)")
                
                choice = input("\nEnter your choice (1 or 2): ").strip()
                
                if choice != "2":
                    print("\n✅ Exiting safely. No changes made to database.")
                    return
                
                # Double confirmation for option 2
                print("\n⚠️  FINAL WARNING: This may cause data loss!")
                confirm = input("Type 'DELETE AND PROCEED' to continue: ").strip()
                
                if confirm != "DELETE AND PROCEED":
                    print("\n✅ Exiting safely. No changes made to database.")
                    return
                
                # Log the dangerous action
                print(f"\n⚠️  User confirmed database reset at {datetime.utcnow()}")
    
    # Initialize database
    print("\n🔄 Initializing database tables...")
    try:
        init_db()
        print("✅ Database tables created successfully!")
        
        # Verify tables were created
        with Session(engine) as session:
            result = session.exec(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """))
            tables = result.all()
            print(f"\n📊 Created {len(tables)} tables:")
            for table in tables:
                print(f"  - {table[0]}")
                
    except Exception as e:
        print(f"\n❌ Error initializing database: {e}")
        print("Please check your database connection and permissions.")
        sys.exit(1)


if __name__ == "__main__":
    safe_init_database()