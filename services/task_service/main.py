# Copyright (c) 2025 Acarin Inc. All rights reserved.
# Proprietary and confidential.
"""Task Service - Microservice for task management and routing."""

import importlib
import os
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlmodel import SQLModel, Session, create_engine, Field, select
import logging
# from task_service import assign_task_logic, complete_task_logic, create_task_logic, delete_task_logic, get_task_logic, list_tasks_logic, update_task_logic

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/tasksmind_tasks")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8001"))
API_GATEWAY_URL = os.getenv("API_GATEWAY_URL", "http://localhost:8000")

# Database setup
engine = create_engine(DATABASE_URL, echo=False)

def get_session():
    with Session(engine) as session:
        yield session

def get_task_logic_func(func_name: str):
    module = importlib.import_module("services.task_service.task_service")  # make sure this is the correct module path
    return getattr(module, func_name)

# Data Models
class Task(SQLModel, table=True):
    id: str = Field(primary_key=True)
    title: str
    description: Optional[str] = None
    priority: str = "medium"  # high, medium, low
    status: str = "pending"  # pending, assigned, approved, completed, rejected
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    due_date: Optional[datetime] = None
    
    # Ownership and assignment
    created_by: Optional[str] = None  # User ID
    assigned_to: Optional[str] = None  # User ID
    approved_by: Optional[str] = None  # User ID
    tenant_id: str  # Tenant ID for multi-tenancy
    org_unit_id: Optional[str] = None  # Organization unit
    
    # Routing and priority
    priority_score: float = 0.5
    routing_rules: Optional[str] = None  # JSON string for routing configuration

# API Models
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    due_date: Optional[datetime] = None
    org_unit_id: Optional[str] = None
    tenant_id: str

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[datetime] = None
    assigned_to: Optional[str] = None

class TaskRead(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    priority: str
    status: str
    created_at: datetime
    updated_at: datetime
    due_date: Optional[datetime] = None
    created_by: Optional[str] = None
    assigned_to: Optional[str] = None
    approved_by: Optional[str] = None
    tenant_id: str
    org_unit_id: Optional[str] = None
    priority_score: float

    class Config:
        from_attributes = True

# FastAPI application
app = FastAPI(
    title="Task Service",
    description="Microservice for task management and routing",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables
@app.on_event("startup")
def create_tables():
    SQLModel.metadata.create_all(engine)
    logger.info("Task Service database tables created")

# Health check
@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "task-service", "port": SERVICE_PORT}

# Task CRUD operations
@app.post("/tasks", response_model=TaskRead)
def create_task(task_data: TaskCreate, session: Session = Depends(get_session)):
    func = get_task_logic_func("create_task_logic")
    return func(task_data.dict(), session)


@app.get("/tasks", response_model=List[TaskRead])
def list_tasks(
    tenant_id: str,
    status: Optional[str] = None,
    assigned_to: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session)
):
    func = get_task_logic_func("list_tasks_logic")
    return func(
        session=session,
        tenant_id=tenant_id,
        status=status,
        assigned_to=assigned_to,
        skip=skip,
        limit=limit
    )


@app.get("/tasks/{task_id}", response_model=TaskRead)
def get_task(task_id: str, session: Session = Depends(get_session)):
    func = get_task_logic_func("get_task_logic")
    return func(task_id, session)


@app.put("/tasks/{task_id}", response_model=TaskRead)
def update_task(task_id: str, task_update: TaskUpdate, session: Session = Depends(get_session)):
    func = get_task_logic_func("update_task_logic")
    return func(task_id, task_update.model_dump(exclude_unset=True), session)


@app.delete("/tasks/{task_id}")
def delete_task(task_id: str, session: Session = Depends(get_session)):
    func = get_task_logic_func("delete_task_logic")
    return func(task_id, session)


@app.post("/tasks/{task_id}/assign")
def assign_task(task_id: str, assigned_to: str, session: Session = Depends(get_session)):
    func = get_task_logic_func("assign_task_logic")
    return func(task_id, assigned_to, session)


@app.post("/tasks/{task_id}/complete")
def complete_task(task_id: str, session: Session = Depends(get_session)):
    func = get_task_logic_func("complete_task_logic")
    return func(task_id, session)

# Metrics endpoint
@app.get("/metrics")
def get_metrics():
    """Basic metrics for monitoring."""
    return {
        "service": "task-service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)