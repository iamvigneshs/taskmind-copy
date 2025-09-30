# Copyright (c) 2025 Acarin Inc. All rights reserved.
# Proprietary and confidential.
"""Assignment Service - Microservice for task assignments and approvals."""

import importlib
import os
import uuid
import httpx
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
# from assignment_service import complete_assignment_logic, create_approval_logic, create_assignment_logic, get_assignment_logic, list_approvals_logic, list_assignments_logic, route_assignment_logic
from sqlmodel import SQLModel, Session, create_engine, Field, select
import logging



# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/tasksmind_assignments")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8004"))
# TASK_SERVICE_URL = os.getenv("TASK_SERVICE_URL", "http://localhost:8001")
# USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://localhost:8002")

# Database setup
engine = create_engine(DATABASE_URL, echo=False)

def get_logic_function(func_name: str):
    module = importlib.import_module("services.assignment_service.assignment_service")  # change if module path differs
    return getattr(module, func_name)

def get_session():
    with Session(engine) as session:
        yield session

# Data Models
class Assignment(SQLModel, table=True):
    id: str = Field(primary_key=True)
    task_id: str
    assigned_to: str  # User ID
    assigned_by: str  # User ID
    tenant_id: str
    
    status: str = "pending"  # pending, accepted, completed, rejected
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    note: Optional[str] = None  # Assignment note
    priority: str = "medium"

class Approval(SQLModel, table=True):
    id: str = Field(primary_key=True)
    task_id: str
    assignment_id: str
    approver_id: str  # User ID
    tenant_id: str
    
    status: str = "pending"  # pending, approved, rejected
    approved_at: Optional[datetime] = None
    approval_note: Optional[str] = None
    
    # Authority and compliance
    authority_level: Optional[str] = None
    requires_additional_approval: bool = False

# API Models
class AssignmentCreate(BaseModel):
    task_id: str
    assigned_to: str
    tenant_id: str
    due_date: Optional[datetime] = None
    note: Optional[str] = None
    priority: str = "medium"

class AssignmentRead(BaseModel):
    id: str
    task_id: str
    assigned_to: str
    assigned_by: str
    tenant_id: str
    status: str
    assigned_at: datetime
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    note: Optional[str] = None
    priority: str

    class Config:
        from_attributes = True

class ApprovalCreate(BaseModel):
    task_id: str
    assignment_id: str
    tenant_id: str
    authority_level: Optional[str] = None

class ApprovalUpdate(BaseModel):
    status: str  # approved, rejected
    approval_note: Optional[str] = None

class ApprovalRead(BaseModel):
    id: str
    task_id: str
    assignment_id: str
    approver_id: str
    tenant_id: str
    status: str
    approved_at: Optional[datetime] = None
    approval_note: Optional[str] = None
    authority_level: Optional[str] = None
    requires_additional_approval: bool

    class Config:
        from_attributes = True

# FastAPI application
app = FastAPI(
    title="Assignment Service",
    description="Microservice for task assignments and approvals",
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
    logger.info("Assignment Service database tables created")

# Health check
@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "assignment-service", "port": SERVICE_PORT}

# Assignment operations
@app.post("/assignments", response_model=AssignmentRead)
def create_assignment(assignment_data: AssignmentCreate, session: Session = Depends(get_session)):
    func = get_logic_function("create_assignment_logic")
    return func(assignment_data.dict(), session)


@app.get("/assignments", response_model=List[AssignmentRead])
def list_assignments(
    tenant_id: str,
    session: Session = Depends(get_session),
    assigned_to: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    func = get_logic_function("list_assignments_logic")
    return func(session, tenant_id, assigned_to, status, skip, limit)


@app.get("/assignments/{assignment_id}", response_model=AssignmentRead)
def get_assignment(assignment_id: str, session: Session = Depends(get_session)):
    func = get_logic_function("get_assignment_logic")
    return func(assignment_id, session)


@app.put("/assignments/{assignment_id}/complete")
def complete_assignment(assignment_id: str, session: Session = Depends(get_session)):
    func = get_logic_function("complete_assignment_logic")
    return func(assignment_id, session)


@app.post("/assignments/{assignment_id}/route")
def route_assignment(
    assignment_id: str,
    new_assignee: str,
    session: Session = Depends(get_session),
    route_note: Optional[str] = None
):
    func = get_logic_function("route_assignment_logic")
    return func(assignment_id, new_assignee, route_note or "", session)


# Approvals
@app.post("/approvals", response_model=ApprovalRead)
def create_approval(approval_data: ApprovalCreate, session: Session = Depends(get_session)):
    func = get_logic_function("create_approval_logic")
    return func(approval_data.dict(), session)


@app.get("/approvals", response_model=List[ApprovalRead])
def list_approvals(
    tenant_id: str,
    session: Session = Depends(get_session),
    approver_id: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    func = get_logic_function("list_approvals_logic")
    return func(tenant_id, approver_id, status, skip, limit, session)

# Metrics endpoint
@app.get("/metrics")
def get_metrics():
    """Basic metrics for monitoring."""
    return {
        "service": "assignment-service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)