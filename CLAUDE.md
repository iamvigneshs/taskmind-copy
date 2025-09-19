# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
MissionMind TasksMind - An AI-powered task orchestration system designed for military/defense environments, integrating with ETMS2 and Army 365. The MVP provides smart routing, authority recommendation, and compliance checking for military tasking operations.

## Common Development Commands

### Setup and Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Set up database (SQLite for local development)
export DATABASE_URL="sqlite:///./tasksmind.db"

# For PostgreSQL (production)
export DATABASE_URL="postgresql://username:password@localhost/tasksmind"
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