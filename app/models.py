"""SQLModel ORM models for MissionMind MVP."""
from __future__ import annotations

from datetime import datetime, date
from typing import List, Optional

from sqlalchemy import Column, JSON
from sqlmodel import Field, Relationship, SQLModel


class TaskTagLink(SQLModel, table=True):
    """Association table between tasks and tags."""

    task_id: Optional[str] = Field(default=None, foreign_key="task.id", primary_key=True)
    tag: Optional[str] = Field(default=None, primary_key=True)


class Task(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True, index=True)
    title: str
    description: str
    classification: str = Field(description="U, C, or S classification")
    suspense_date: date
    originator: str
    org_unit_id: str
    priority_score: float = 0.0
    status: str = Field(default="draft")
    record_series_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    tags: List[str] = Field(default_factory=list, sa_column=Column(JSON))

    assignments: List["Assignment"] = Relationship(back_populates="task")
    comments: List["Comment"] = Relationship(back_populates="task")


class Assignment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: str = Field(foreign_key="task.id")
    assignee_type: str = Field(default="org")  # org or user
    assignee_id: str
    role: str
    due_override_date: Optional[date] = None
    state: str = Field(default="pending")
    rationale: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    task: Optional[Task] = Relationship(back_populates="assignments")


class Comment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: str = Field(foreign_key="task.id")
    author_user_id: str
    body: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    parent_comment_id: Optional[int] = Field(default=None, foreign_key="comment.id")

    task: Optional[Task] = Relationship(back_populates="comments")


class OrgUnit(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    name: str
    echelon: str
    parent_id: Optional[str] = Field(default=None, foreign_key="orgunit.id")


class Authority(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    title: str
    org_unit_id: str = Field(foreign_key="orgunit.id")
    grade: str
    authority_scope: List[str] = Field(default_factory=list, sa_column=Column(JSON))


class AuditLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    object_type: str
    object_id: str
    actor_user_id: str
    action: str
    details: dict = Field(default_factory=dict, sa_column=Column(JSON))
    ts: datetime = Field(default_factory=datetime.utcnow)
