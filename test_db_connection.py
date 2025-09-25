#!/usr/bin/env python
"""Test database connection to RDS."""
import os
from dotenv import load_dotenv
from sqlmodel import Session, create_engine, text

# Load environment variables
load_dotenv()

# Get DATABASE_URL directly from environment
DATABASE_URL = os.getenv("DATABASE_URL")

def test_connection():
    """Test database connection and basic operations."""
    if not DATABASE_URL or "sqlite" in DATABASE_URL:
        print("❌ Data Source Connectivity failed")
        print("Error: No valid PostgreSQL DATABASE_URL found in environment")
        print("Please ensure DATABASE_URL is set to your RDS PostgreSQL connection string")
        return False
        
    print(f"Testing connection to RDS...")
    print(f"Host: {DATABASE_URL.split('@')[1].split(':')[0] if '@' in DATABASE_URL else 'Unknown'}")
    print("-" * 50)
    
    try:
        # Create engine
        engine = create_engine(DATABASE_URL)
        
        # Test basic connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✓ Basic connection successful")
            
            # Get PostgreSQL version
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✓ PostgreSQL version: {version.split(',')[0]}")
            
            # Test current database
            result = conn.execute(text("SELECT current_database()"))
            db_name = result.fetchone()[0]
            print(f"✓ Connected to database: {db_name}")
            
            # Test current user
            result = conn.execute(text("SELECT current_user"))
            user = result.fetchone()[0]
            print(f"✓ Connected as user: {user}")
            
        print("-" * 50)
        
        # Initialize database tables
        print("Initializing database tables...")
        from app.database import init_db
        init_db()
        print("✓ Database tables created/verified")
        
        # Test session creation
        with Session(engine) as session:
            # List tables
            result = session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            print(f"✓ Found {len(tables)} tables:")
            for table in tables:
                print(f"  - {table}")
                
        print("-" * 50)
        print("✓ All database tests passed successfully!")
        
    except Exception as e:
        print("❌ Data Source Connectivity failed")
        print(f"Error: {type(e).__name__}: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_connection()