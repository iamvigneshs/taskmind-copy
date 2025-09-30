# Copyright (c) 2025 Acarin Inc. All rights reserved.
# Proprietary and confidential.
"""Comment Service - Microservice for comments and communication."""

import os
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from comments_service import create_comment_logic, create_status_update_logic, create_task_comment_logic, delete_comment_logic, get_assignment_comments_logic, get_comment_logic, get_comment_thread_logic, get_task_comments_logic, list_comments_logic, update_comment_logic
from sqlmodel import SQLModel, Session, create_engine, Field, select
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/tasksmind_comments")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", "8005"))

# Database setup
engine = create_engine(DATABASE_URL, echo=False)

def get_session():
    with Session(engine) as session:
        yield session

# Data Models
class Comment(SQLModel, table=True):
    id: str = Field(primary_key=True)
    task_id: str
    assignment_id: Optional[str] = None  # Optional link to specific assignment
    author_id: str  # User ID
    tenant_id: str
    
    content: str
    comment_type: str = "general"  # general, status_update, route_note, approval_note
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Metadata
    is_internal: bool = False  # Internal vs external communication
    visibility: str = "all"  # all, assignees_only, approvers_only
    priority: str = "normal"  # urgent, normal, low

class Attachment(SQLModel, table=True):
    id: str = Field(primary_key=True)
    comment_id: str
    filename: str
    file_path: str
    file_size: int
    content_type: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    uploaded_by: str  # User ID

# API Models
class CommentCreate(BaseModel):
    task_id: str
    content: str
    tenant_id: str
    assignment_id: Optional[str] = None
    comment_type: str = "general"
    is_internal: bool = False
    visibility: str = "all"
    priority: str = "normal"

class CommentUpdate(BaseModel):
    content: Optional[str] = None
    visibility: Optional[str] = None
    priority: Optional[str] = None

class CommentRead(BaseModel):
    id: str
    task_id: str
    assignment_id: Optional[str] = None
    author_id: str
    tenant_id: str
    content: str
    comment_type: str
    created_at: datetime
    updated_at: datetime
    is_internal: bool
    visibility: str
    priority: str

    class Config:
        from_attributes = True

class AttachmentRead(BaseModel):
    id: str
    comment_id: str
    filename: str
    file_size: int
    content_type: str
    uploaded_at: datetime
    uploaded_by: str

    class Config:
        from_attributes = True

# FastAPI application
app = FastAPI(
    title="Comment Service",
    description="Microservice for comments and communication",
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
    logger.info("Comment Service database tables created")

# Health check
@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "comment-service", "port": SERVICE_PORT}

# Comment operations
@app.post("/comments", response_model=CommentRead)
def create_comment(comment_data: CommentCreate, session):
    return create_comment_logic(comment_data.dict(), session)

@app.get("/comments", response_model=List[CommentRead])
def list_comments(
    tenant_id: str,
    task_id: Optional[str] = None,
    assignment_id: Optional[str] = None,
    author_id: Optional[str] = None,
    comment_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session)
):
    return list_comments_logic(session, tenant_id, task_id, assignment_id, author_id, comment_type, skip, limit)

@app.get("/comments/{comment_id}", response_model=CommentRead)
def get_comment(comment_id: str, session):
    return get_comment_logic(comment_id, session)

@app.put("/comments/{comment_id}", response_model=CommentRead)
def update_comment(comment_id: str, comment_update: CommentUpdate, session: Session = Depends(get_session)):
    return update_comment_logic(comment_id, comment_update.model_dump(exclude_unset=True), session)


@app.delete("/comments/{comment_id}")
def delete_comment(comment_id: str, session):
    return delete_comment_logic(comment_id, session)

# Task-specific comment operations
@app.get("/tasks/{task_id}/comments", response_model=List[CommentRead])
def get_task_comments(
    task_id: str,
    tenant_id: str,
    comment_type: Optional[str] = None,
    visibility: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """Get all comments for a specific task using business logic."""
    comments = get_task_comments_logic(
        session=session,
        task_id=task_id,
        tenant_id=tenant_id,
        comment_type=comment_type,
        visibility=visibility
    )
    
    logger.info(f"Retrieved {len(comments)} comments for task {task_id}")
    return comments

@app.post("/tasks/{task_id}/comments", response_model=CommentRead)
def create_task_comment(
    task_id: str,
    comment_data: CommentCreate,
    session
):
    return create_task_comment_logic(task_id, comment_data, session)


@app.get("/assignments/{assignment_id}/comments", response_model=List[CommentRead])
def get_assignment_comments(
    assignment_id: str,
    tenant_id: str,
    session
):
    return get_assignment_comments_logic(assignment_id, tenant_id, session)


@app.get("/comments/{comment_id}/thread", response_model=List[CommentRead])
def get_comment_thread(
    comment_id: str,
    session
):
    return get_comment_thread_logic(comment_id, session)

# Status update comments
@app.post("/tasks/{task_id}/status-update", response_model=CommentRead)
def create_status_update(
    task_id: str,
    status: str,
    note: str,
    tenant_id: str,
    session
):
    return create_status_update_logic(task_id, status, note, tenant_id, session)

# Metrics endpoint
@app.get("/metrics")
def get_metrics():
    """Basic metrics for monitoring."""
    return {
        "service": "comment-service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)