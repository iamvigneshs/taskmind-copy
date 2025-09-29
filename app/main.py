# Copyright (c) 2025 Acarin Inc. All rights reserved.
# Proprietary and confidential.
"""MissionMind TasksMind - Multi-tenant FastAPI application."""
from __future__ import annotations

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlmodel import Session

from app.database import init_db, get_session
from app.dependencies import get_or_create_dev_user
from app.routers.tenants import router as tenants_router
from app.routers.users import router as users_router
from app.routers.orgunits import router as orgunits_router
from app.routers.tasks import router as tasks_router
# from app.routers.templates import router as templates_router  # Temporarily disabled


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    print("🚀 Starting MissionMind TasksMind...")
    init_db()
    print("✅ Database initialized")
    yield
    print("👋 Shutting down MissionMind TasksMind")


app = FastAPI(
    title="MissionMind TasksMind API",
    description="Multi-tenant task orchestration system for military, government, and commercial organizations",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers - Enable tasks router for microservices workflow
app.include_router(tasks_router, prefix="/api/v2")
# Other routers temporarily disabled until database schema is fixed
# app.include_router(tenants_router, prefix="/api/v2")
# app.include_router(users_router, prefix="/api/v2")
# app.include_router(orgunits_router, prefix="/api/v2")
# app.include_router(templates_router, prefix="/api/v2")  # Temporarily disabled


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "MissionMind TasksMind API v2.0",
        "description": "Multi-tenant task orchestration system",
        "docs": "/docs",
        "health": "/healthz"
    }


@app.get("/healthz")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "2.0.0"}


@app.get("/api/v2/info")
def api_info(session: Session = Depends(get_session)):
    """API information and basic statistics."""
    from app.models import User, Tenant
    from sqlmodel import select
    
    try:
        user_count = len(session.exec(select(User)).all())
        tenant_count = len(session.exec(select(Tenant)).all())
        database_status = "connected"
    except Exception as e:
        user_count = 0
        tenant_count = 0
        database_status = f"error: {str(e)}"
    
    return {
        "version": "2.0.0",
        "multi_tenant": True,
        "supported_org_types": [
            "military", "government", "enterprise", "small_business",
            "nonprofit", "startup", "consulting", "healthcare",
            "education", "legal", "financial", "technology"
        ],
        "database_status": database_status,
        "statistics": {
            "users": user_count,
            "tenants": tenant_count
        },
        "message": "MissionMind TasksMind API is running with simplified multi-tenant models"
    }


# Development endpoint to create sample data
@app.post("/api/v2/dev/setup")
def setup_dev_environment():
    """Create development environment with sample data."""
    return {
        "message": "Development environment setup available",
        "note": "Database schema migration needed - tenant_id column missing",
        "next_steps": [
            "Fix database schema migration",
            "Add tenant_id columns to existing tables", 
            "Create sample tenant and user data"
        ]
    }


# Basic working endpoints without database dependencies
@app.get("/api/v2/status")
def system_status():
    """System status and configuration."""
    return {
        "status": "operational",
        "version": "2.0.0",
        "api_mode": "simplified",
        "database_migration": "pending",
        "available_endpoints": [
            "GET /",
            "GET /healthz", 
            "GET /api/v2/info",
            "GET /api/v2/status",
            "POST /api/v2/dev/setup",
            "GET /docs"
        ]
    }


@app.get("/api/v2/schema")
def database_schema_info():
    """Database schema information and migration status."""
    return {
        "current_issue": "tenant_id column missing from user table",
        "required_migrations": [
            {
                "table": "user",
                "missing_columns": ["tenant_id", "first_name", "last_name", "title", "employee_id", "is_tenant_admin", "is_system_admin", "is_active"],
                "status": "needed"
            },
            {
                "table": "orgunit", 
                "missing_columns": ["tenant_id", "updated_at", "level", "path"],
                "status": "completed"
            }
        ],
        "next_action": "Run database migration script to add missing columns"
    }
