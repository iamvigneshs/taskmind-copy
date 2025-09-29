# Copyright (c) 2025 Acarin Inc. All rights reserved.
# Proprietary and confidential.
"""Task management API routes - Core workflow microservice."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from pydantic import BaseModel

from ..database import get_session

router = APIRouter(prefix="/tasks", tags=["tasks"])


# Simplified task schemas for the workflow
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    priority: str = "medium"  # high, medium, low
    due_date: Optional[datetime] = None


class TaskCreate(TaskBase):
    pass


class TaskRead(TaskBase):
    id: str
    status: str  # pending, assigned, approved, completed, rejected
    created_at: datetime
    created_by: Optional[str] = None
    assigned_to: Optional[str] = None
    approved_by: Optional[str] = None
    tenant_id: Optional[str] = None
    
    class Config:
        from_attributes = True


class TaskAssign(BaseModel):
    assigned_to: str
    note: Optional[str] = None


class TaskApproval(BaseModel):
    approved: bool
    note: Optional[str] = None


class CommentCreate(BaseModel):
    content: str


class CommentRead(BaseModel):
    id: str
    task_id: str
    content: str
    author: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class RouteRequest(BaseModel):
    route_to: str
    note: Optional[str] = None


# Basic endpoints for the workflow: Create → Assign → Approve → Comment → Route
@router.post("/", response_model=TaskRead)
def create_task(task_in: TaskCreate, session: Session = Depends(get_session)):
    """Create a new task."""
    # Generate a simple task ID
    task_id = f"T-25-{datetime.now().strftime('%H%M%S')}"
    
    # Mock task creation - will be replaced with actual database operations
    task_data = task_in.model_dump()
    task_data.update({
        "id": task_id,
        "status": "pending",
        "created_at": datetime.now(),
        "created_by": "system",  # Will be current user when auth is enabled
        "assigned_to": None,
        "approved_by": None,
        "tenant_id": "default-tenant"
    })
    return TaskRead(**task_data)


@router.get("/", response_model=List[TaskRead])
def list_tasks(
    status: Optional[str] = Query(None, description="Filter by status"),
    assigned_to_me: bool = Query(False, description="Show tasks assigned to current user"),
    session: Session = Depends(get_session)
):
    """List tasks with optional filters."""
    # Mock data for now - will be replaced with actual database queries
    tasks = [
        TaskRead(
            id="T-25-001",
            title="Configure Organization Templates", 
            description="Set up configurable organization level templates for military and commercial use",
            priority="high",
            status="pending",
            created_at=datetime.now(),
            created_by="system",
            due_date=None,
            tenant_id="default-tenant"
        ),
        TaskRead(
            id="T-25-002",
            title="Implement Task Assignment Workflow",
            description="Build the core task assignment and approval workflow",
            priority="medium", 
            status="assigned",
            created_at=datetime.now(),
            created_by="system",
            assigned_to="dev-user",
            due_date=None,
            tenant_id="default-tenant"
        )
    ]
    
    # Apply filters
    if status:
        tasks = [t for t in tasks if t.status == status]
    
    return tasks


@router.get("/{task_id}", response_model=TaskRead)
def get_task(task_id: str, session: Session = Depends(get_session)):
    """Get a specific task by ID."""
    # Mock response for now
    if task_id == "T-25-001":
        return TaskRead(
            id="T-25-001",
            title="Configure Organization Templates",
            description="Set up configurable organization level templates for military and commercial use",
            priority="high",
            status="pending",
            created_at=datetime.now(),
            created_by="system",
            due_date=None,
            tenant_id="default-tenant"
        )
    elif task_id == "T-25-002":
        return TaskRead(
            id="T-25-002",
            title="Implement Task Assignment Workflow",
            description="Build the core task assignment and approval workflow",
            priority="medium",
            status="assigned",
            created_at=datetime.now(),
            created_by="system",
            assigned_to="dev-user",
            due_date=None,
            tenant_id="default-tenant"
        )
    else:
        raise HTTPException(status_code=404, detail="Task not found")


@router.post("/{task_id}/assign", response_model=TaskRead)
def assign_task(
    task_id: str,
    assignment: TaskAssign,
    session: Session = Depends(get_session)
):
    """Assign a task to a user."""
    return TaskRead(
        id=task_id,
        title="Sample Task (Assigned)",
        description="Task has been assigned",
        priority="high",
        status="assigned",
        created_at=datetime.now(),
        created_by="system",
        assigned_to=assignment.assigned_to,
        due_date=None,
        tenant_id="default-tenant"
    )


@router.post("/{task_id}/approve", response_model=TaskRead)
def approve_task(
    task_id: str,
    approval: TaskApproval,
    session: Session = Depends(get_session)
):
    """Approve or reject a task."""
    status = "approved" if approval.approved else "rejected"
    return TaskRead(
        id=task_id,
        title="Sample Task (Processed)",
        description="Task has been processed",
        priority="high",
        status=status,
        created_at=datetime.now(),
        created_by="system",
        approved_by="approver-user",
        due_date=None,
        tenant_id="default-tenant"
    )


@router.post("/{task_id}/comments", response_model=CommentRead)
def add_comment(
    task_id: str,
    comment: CommentCreate,
    session: Session = Depends(get_session)
):
    """Add a comment to a task."""
    return CommentRead(
        id=f"C-{datetime.now().strftime('%H%M%S')}",
        task_id=task_id,
        content=comment.content,
        author="current-user",
        created_at=datetime.now()
    )


@router.get("/{task_id}/comments", response_model=List[CommentRead])
def get_task_comments(task_id: str, session: Session = Depends(get_session)):
    """Get all comments for a task."""
    return [
        CommentRead(
            id="C-001",
            task_id=task_id,
            content="This is a sample comment",
            author="user1",
            created_at=datetime.now()
        ),
        CommentRead(
            id="C-002", 
            task_id=task_id,
            content="Another comment with progress update",
            author="user2",
            created_at=datetime.now()
        )
    ]


@router.post("/{task_id}/route", response_model=TaskRead)
def route_task(
    task_id: str,
    route_data: RouteRequest,
    session: Session = Depends(get_session)
):
    """Route a task to another user with a note."""    
    return TaskRead(
        id=task_id,
        title="Sample Task (Routed)",
        description=f"Task routed: {route_data.note or 'No note provided'}",
        priority="high",
        status="assigned",
        created_at=datetime.now(),
        created_by="system",
        assigned_to=route_data.route_to,
        due_date=None,
        tenant_id="default-tenant"
    )
