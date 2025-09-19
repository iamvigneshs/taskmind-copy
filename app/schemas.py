"""Pydantic schemas for MissionMind MVP APIs."""
from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class AssignmentBase(BaseModel):
    assignee_type: str = Field(default="org")
    assignee_id: str
    role: str
    due_override_date: Optional[date] = None
    state: str = Field(default="pending")
    rationale: Optional[str] = None


class AssignmentCreate(AssignmentBase):
    pass


class AssignmentRead(AssignmentBase):
    id: int
    task_id: str
    created_at: datetime

    class Config:
        orm_mode = True


class CommentBase(BaseModel):
    author_user_id: str
    body: str
    parent_comment_id: Optional[int] = None


class CommentCreate(CommentBase):
    pass


class CommentRead(CommentBase):
    id: int
    task_id: str
    created_at: datetime

    class Config:
        orm_mode = True


class TaskBase(BaseModel):
    title: str
    description: str
    classification: str
    suspense_date: date
    originator: str
    org_unit_id: str
    record_series_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class TaskCreate(TaskBase):
    id: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    classification: Optional[str] = None
    suspense_date: Optional[date] = None
    originator: Optional[str] = None
    org_unit_id: Optional[str] = None
    record_series_id: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None


class TaskRead(TaskBase):
    id: str
    priority_score: float
    status: str
    created_at: datetime
    updated_at: datetime
    assignments: List[AssignmentRead] = Field(default_factory=list)

    class Config:
        orm_mode = True


class AuthoritySuggestion(BaseModel):
    authority_id: str
    title: str
    org_unit_id: str
    grade: str
    confidence: float
    rationale: str


class TaskSummary(BaseModel):
    summary: str
    risk_level: str
    key_points: List[str]


class RiskInsight(BaseModel):
    task_id: str
    risk_level: str
    late_probability: float
    drivers: List[str]
    recommended_actions: List[str]


class TaskListFilters(BaseModel):
    status: Optional[str] = None
    due_before: Optional[date] = None
    org: Optional[str] = None


class QualityIssue(BaseModel):
    code: str
    severity: str
    message: str


class QualityCheckResult(BaseModel):
    task_id: str
    issues: List[QualityIssue]
    passed: bool
