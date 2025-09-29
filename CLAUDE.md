# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## CRITICAL DATABASE SAFETY RULES

### 🚨 DATABASE PROTECTION IS PARAMOUNT 🚨

1. **ALWAYS USE THE REMOTE RDS DATABASE** - Never use SQLite for any operations
2. **NEVER DELETE OR DROP** tables, databases, or data without explicit user permission
3. **ALWAYS ASK PERMISSION** before:
   - Running DELETE, DROP, TRUNCATE commands
   - Modifying table structures (ALTER TABLE)
   - Running any database migration that removes columns or tables
   - Executing scripts that could affect existing data
4. **USE TRANSACTIONS** for all data modifications with proper rollback handling
5. **ALWAYS BACKUP** before any structural changes (ask user to confirm backup exists)
6. **READ-ONLY FIRST** - When exploring database, use SELECT statements only
7. **USE LIMIT** clauses when querying to prevent performance issues
8. **NEVER COMMIT** destructive changes without showing the user exactly what will be affected

### Database Connection
- **REQUIRED**: Always use the RDS PostgreSQL connection from .env file
- **FORBIDDEN**: Using SQLite or any local database
- **CHECK**: Verify DATABASE_URL starts with "postgresql://" before any operation
- **REFERENCE**: See DATABASE_SAFETY.md for detailed safety guidelines

## Project Overview
MissionMind TasksMind - An AI-powered task orchestration system designed for military/defense environments, integrating with ETMS2 and Army 365. The MVP provides smart routing, authority recommendation, and compliance checking for military tasking operations.

## Common Development Commands

### Setup and Installation
```bash
# Install dependencies in virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# IMPORTANT: Always use RDS PostgreSQL database
# The DATABASE_URL is already configured in .env file
# DO NOT use SQLite or modify the DATABASE_URL

# Load environment variables
source .env  # or use python-dotenv
```

### Running the Application
```bash
# Start the development server
uvicorn app.main:app --reload

# Access the API documentation
# http://localhost:8000/docs
```

### Testing
```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=app

# Run specific test file
pytest app/tests/test_tasks.py

# Run with verbose output
pytest -v
```

### Database Operations
```bash
# Generate synthetic test data
python scripts/generate_synthetic_data.py

# The database will auto-create tables on first run
```

## High-Level Architecture

### Core Components
1. **API Layer** (FastAPI)
   - `app/main.py`: Application entry point
   - `app/routers/tasks.py`: Task management endpoints

2. **Data Models** (SQLModel/SQLAlchemy)
   - `app/models.py`: ORM models (Task, Assignment, OrgUnit, Authority)
   - `app/schemas.py`: Pydantic schemas for API validation
   - `app/database.py`: Database session management

3. **Business Logic Services**
   - `app/services/routing.py`: Priority scoring and smart routing algorithms
   - `app/services/authority.py`: Authority recommendation engine
   - `app/services/summarizer.py`: Task summarization (currently heuristic-based)

### Key Design Patterns
- **Dependency Injection**: Database sessions injected via FastAPI dependencies
- **Repository Pattern**: Clean separation between data models and business logic
- **Service Layer**: Business logic encapsulated in service modules
- **Schema Validation**: Pydantic models for request/response validation

### Task ID Format
Tasks use format: `T-{YEAR}-{XXXXXX}` (e.g., T-25-000001)

### Testing Strategy
- Uses pytest with pytest-asyncio for async operations
- In-memory SQLite for test isolation
- FastAPI TestClient for endpoint testing
- Override dependencies for test database sessions

## Important Context
- Built for military compliance (AR 25-50, ARIMS)
- Supports classification levels (U/C/S)
- Designed for future LLM integration (currently using heuristics)
- PostgreSQL recommended for production deployment