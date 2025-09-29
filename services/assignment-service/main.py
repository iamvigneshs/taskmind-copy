# Copyright (c) 2025 Acarin Inc. All rights reserved.
# Proprietary and confidential.
"""Assignment Service - Microservice for task assignments and approvals."""

import os
import uuid
import httpx
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlmodel import SQLModel, Session, create_engine, Field, select
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/tasksmind_assignments")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8004"))
TASK_SERVICE_URL = os.getenv("TASK_SERVICE_URL", "http://localhost:8001")
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://localhost:8002")

# Database setup
engine = create_engine(DATABASE_URL, echo=False)

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
async def create_assignment(assignment_data: AssignmentCreate, session: Session = Depends(get_session)):
    """Create a new task assignment."""
    assignment_id = f"A-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"
    
    # Verify task exists by calling Task Service
    async with httpx.AsyncClient() as client:
        try:
            task_response = await client.get(f"{TASK_SERVICE_URL}/tasks/{assignment_data.task_id}")
            if task_response.status_code != 200:
                raise HTTPException(status_code=404, detail="Task not found")
        except httpx.RequestError:
            logger.warning("Could not verify task with Task Service - proceeding anyway")
    
    assignment = Assignment(
        id=assignment_id,
        task_id=assignment_data.task_id,
        assigned_to=assignment_data.assigned_to,
        assigned_by="system",  # Will be replaced with authenticated user
        tenant_id=assignment_data.tenant_id,
        due_date=assignment_data.due_date,
        note=assignment_data.note,
        priority=assignment_data.priority
    )
    
    session.add(assignment)
    session.commit()
    session.refresh(assignment)
    
    # Update task status in Task Service
    async with httpx.AsyncClient() as client:
        try:
            await client.put(
                f"{TASK_SERVICE_URL}/tasks/{assignment_data.task_id}",
                json={"assigned_to": assignment_data.assigned_to, "status": "assigned"}
            )
        except httpx.RequestError:
            logger.warning("Could not update task status in Task Service")
    
    logger.info(f"Created assignment {assignment_id} for task {assignment_data.task_id}")
    return assignment

@app.get("/assignments", response_model=List[AssignmentRead])
def list_assignments(
    tenant_id: str,
    assigned_to: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session)
):
    """List assignments with filters."""
    query = select(Assignment).where(Assignment.tenant_id == tenant_id)
    
    if assigned_to:
        query = query.where(Assignment.assigned_to == assigned_to)
    if status:
        query = query.where(Assignment.status == status)
    
    query = query.offset(skip).limit(limit)
    assignments = session.exec(query).all()
    
    logger.info(f"Retrieved {len(assignments)} assignments for tenant {tenant_id}")
    return assignments

@app.get("/assignments/{assignment_id}", response_model=AssignmentRead)
def get_assignment(assignment_id: str, session: Session = Depends(get_session)):
    """Get a specific assignment."""
    assignment = session.get(Assignment, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment

@app.put("/assignments/{assignment_id}/complete")
async def complete_assignment(assignment_id: str, session: Session = Depends(get_session)):
    """Mark an assignment as completed."""
    assignment = session.get(Assignment, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    assignment.status = "completed"
    assignment.completed_at = datetime.utcnow()
    
    session.add(assignment)
    session.commit()
    session.refresh(assignment)
    
    # Update task status in Task Service
    async with httpx.AsyncClient() as client:
        try:
            await client.put(
                f"{TASK_SERVICE_URL}/tasks/{assignment.task_id}",
                json={"status": "completed"}
            )
        except httpx.RequestError:
            logger.warning("Could not update task status in Task Service")
    
    logger.info(f"Completed assignment {assignment_id}")
    return assignment

# Approval operations
@app.post("/approvals", response_model=ApprovalRead)
def create_approval(approval_data: ApprovalCreate, session: Session = Depends(get_session)):
    """Create a new approval request."""
    approval_id = f"AP-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"
    
    approval = Approval(
        id=approval_id,
        task_id=approval_data.task_id,
        assignment_id=approval_data.assignment_id,
        approver_id="system",  # Will be replaced with authenticated user
        tenant_id=approval_data.tenant_id,
        authority_level=approval_data.authority_level
    )
    
    session.add(approval)
    session.commit()
    session.refresh(approval)
    
    logger.info(f"Created approval {approval_id} for task {approval_data.task_id}")
    return approval

@app.get("/approvals", response_model=List[ApprovalRead])
def list_approvals(
    tenant_id: str,
    approver_id: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session)
):
    """List approvals with filters."""
    query = select(Approval).where(Approval.tenant_id == tenant_id)
    
    if approver_id:
        query = query.where(Approval.approver_id == approver_id)
    if status:
        query = query.where(Approval.status == status)
    
    query = query.offset(skip).limit(limit)
    approvals = session.exec(query).all()
    
    logger.info(f"Retrieved {len(approvals)} approvals for tenant {tenant_id}")
    return approvals

@app.put("/approvals/{approval_id}")
async def update_approval(
    approval_id: str, 
    approval_update: ApprovalUpdate, 
    session: Session = Depends(get_session)
):
    """Approve or reject an approval request."""
    approval = session.get(Approval, approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    approval.status = approval_update.status
    approval.approval_note = approval_update.approval_note
    approval.approved_at = datetime.utcnow()
    
    session.add(approval)
    session.commit()
    session.refresh(approval)
    
    # Update task status based on approval
    new_task_status = "approved" if approval_update.status == "approved" else "rejected"
    async with httpx.AsyncClient() as client:
        try:
            await client.put(
                f"{TASK_SERVICE_URL}/tasks/{approval.task_id}",
                json={"status": new_task_status}
            )
        except httpx.RequestError:
            logger.warning("Could not update task status in Task Service")
    
    logger.info(f"Updated approval {approval_id} to {approval_update.status}")
    return approval

# Workflow operations
@app.post("/assignments/{assignment_id}/route")
async def route_assignment(
    assignment_id: str,
    new_assignee: str,
    route_note: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """Route an assignment to a different user."""
    assignment = session.get(Assignment, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    # Create new assignment
    new_assignment_id = f"A-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"
    new_assignment = Assignment(
        id=new_assignment_id,
        task_id=assignment.task_id,
        assigned_to=new_assignee,
        assigned_by=assignment.assigned_to,  # Previous assignee becomes the assigner
        tenant_id=assignment.tenant_id,
        due_date=assignment.due_date,
        note=f"Routed from {assignment.assigned_to}: {route_note or 'No note'}",
        priority=assignment.priority
    )
    
    # Mark old assignment as completed
    assignment.status = "completed"
    assignment.completed_at = datetime.utcnow()
    
    session.add(assignment)
    session.add(new_assignment)
    session.commit()
    session.refresh(new_assignment)
    
    # Update task assignment in Task Service
    async with httpx.AsyncClient() as client:
        try:
            await client.put(
                f"{TASK_SERVICE_URL}/tasks/{assignment.task_id}",
                json={"assigned_to": new_assignee}
            )
        except httpx.RequestError:
            logger.warning("Could not update task assignment in Task Service")
    
    logger.info(f"Routed assignment {assignment_id} to new assignment {new_assignment_id}")
    return new_assignment

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