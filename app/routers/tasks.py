"""Task-related API routes."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from ..database import get_session
from ..models import Assignment, Authority, Comment, OrgUnit, Task
from ..schemas import (
    AssignmentCreate,
    AssignmentRead,
    AuthoritySuggestion,
    CommentCreate,
    CommentRead,
    QualityCheckResult,
    QualityIssue,
    RiskInsight,
    TaskCreate,
    TaskRead,
    TaskSummary,
    TaskUpdate,
)
from ..services import authority as authority_service
from ..services import routing as routing_service
from ..services import summarizer as summarizer_service

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _generate_task_id(session: Session) -> str:
    existing = session.exec(select(Task.id)).all()
    seq = len(existing) + 1
    return f"T-25-{seq:06d}"


def _load_task(session: Session, task_id: str) -> Task:
    statement = select(Task).where(Task.id == task_id)
    task = session.exec(statement).one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/", response_model=TaskRead)
def create_task(task_in: TaskCreate, session: Session = Depends(get_session)) -> TaskRead:
    task_data = task_in.dict()
    task_id = task_data.get("id") or _generate_task_id(session)
    task_data["id"] = task_id
    task = Task(**task_data)
    task.priority_score = routing_service.compute_priority(task)
    task.status = "open"
    task.created_at = datetime.utcnow()
    task.updated_at = datetime.utcnow()

    session.add(task)
    session.commit()

    # auto-generate routing assignment
    assignment = routing_service.generate_assignment(task, session)
    session.add(assignment)
    session.commit()

    session.refresh(task)
    # eager load assignments
    task = _load_task(session, task.id)
    _ = task.assignments
    return TaskRead.from_orm(task)


@router.get("/", response_model=List[TaskRead])
def list_tasks(
    status: Optional[str] = Query(None),
    due_before: Optional[datetime] = Query(None),
    org: Optional[str] = Query(None),
    session: Session = Depends(get_session),
) -> List[TaskRead]:
    statement = select(Task)
    if status:
        statement = statement.where(Task.status == status)
    if due_before:
        statement = statement.where(Task.suspense_date <= due_before.date())
    if org:
        statement = statement.where(Task.org_unit_id == org)

    tasks = session.exec(statement).all()
    result: List[TaskRead] = []
    for task in tasks:
        _ = task.assignments
        result.append(TaskRead.from_orm(task))
    return result


@router.get("/{task_id}", response_model=TaskRead)
def get_task(task_id: str, session: Session = Depends(get_session)) -> TaskRead:
    task = _load_task(session, task_id)
    _ = task.assignments
    return TaskRead.from_orm(task)


@router.patch("/{task_id}", response_model=TaskRead)
def update_task(task_id: str, task_update: TaskUpdate, session: Session = Depends(get_session)) -> TaskRead:
    task = _load_task(session, task_id)
    update_data = task_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)
    task.updated_at = datetime.utcnow()
    task.priority_score = routing_service.compute_priority(task)
    session.add(task)
    session.commit()
    session.refresh(task)
    _ = task.assignments
    return TaskRead.from_orm(task)


@router.post("/{task_id}/assignments", response_model=AssignmentRead)
def add_assignment(
    task_id: str,
    assignment_in: AssignmentCreate,
    session: Session = Depends(get_session),
) -> AssignmentRead:
    _ = _load_task(session, task_id)
    assignment = Assignment(task_id=task_id, **assignment_in.dict())
    session.add(assignment)
    session.commit()
    session.refresh(assignment)
    return AssignmentRead.from_orm(assignment)


@router.post("/{task_id}/comments", response_model=CommentRead)
def add_comment(
    task_id: str,
    comment_in: CommentCreate,
    session: Session = Depends(get_session),
) -> CommentRead:
    _ = _load_task(session, task_id)
    comment = Comment(task_id=task_id, **comment_in.dict())
    session.add(comment)
    session.commit()
    session.refresh(comment)
    return CommentRead.from_orm(comment)


@router.get("/{task_id}/comments", response_model=List[CommentRead])
def list_comments(task_id: str, session: Session = Depends(get_session)) -> List[CommentRead]:
    _ = _load_task(session, task_id)
    comments = session.exec(select(Comment).where(Comment.task_id == task_id)).all()
    return [CommentRead.from_orm(comment) for comment in comments]


@router.get("/{task_id}/summary", response_model=TaskSummary)
def get_summary(task_id: str, session: Session = Depends(get_session)) -> TaskSummary:
    task = _load_task(session, task_id)
    comments = session.exec(select(Comment.body).where(Comment.task_id == task_id)).all()
    comment_texts = [c[0] if isinstance(c, tuple) else c for c in comments]
    return summarizer_service.summarize_task(task, comment_texts)


@router.get("/{task_id}/authority-suggestions", response_model=List[AuthoritySuggestion])
def get_authority_suggestions(task_id: str, session: Session = Depends(get_session)) -> List[AuthoritySuggestion]:
    task = _load_task(session, task_id)
    return authority_service.suggest_authorities(task, session)


@router.get("/{task_id}/risk", response_model=RiskInsight)
def get_risk(task_id: str, session: Session = Depends(get_session)) -> RiskInsight:
    task = _load_task(session, task_id)
    risk_level = "green"
    late_prob = 0.2
    drivers: List[str] = []
    if task.priority_score >= 0.8:
        risk_level = "red"
        late_prob = 0.75
        drivers.append("High priority score indicates urgency")
    elif task.priority_score >= 0.6:
        risk_level = "amber"
        late_prob = 0.5
        drivers.append("Moderate urgency from suspense/prior history")
    if task.status == "overdue":
        risk_level = "red"
        late_prob = 0.9
        drivers.append("Task already overdue")

    return RiskInsight(
        task_id=task.id,
        risk_level=risk_level,
        late_probability=round(late_prob, 2),
        drivers=drivers or ["No major risk factors detected"],
        recommended_actions=["Confirm staffing plan", "Send reminder via notification service"],
    )


@router.get("/{task_id}/quality-check", response_model=QualityCheckResult)
def run_quality_check(task_id: str, session: Session = Depends(get_session)) -> QualityCheckResult:
    task = _load_task(session, task_id)
    issues: List[QualityIssue] = []
    if len(task.description) < 30:
        issues.append(
            QualityIssue(code="DESC_LEN", severity="medium", message="Description is brief; Army 25-50 recommends more context.")
        )
    if not task.record_series_id:
        issues.append(
            QualityIssue(code="ARIMS_TAG", severity="low", message="ARIMS record series missing; add before final approval.")
        )
    passed = len([i for i in issues if i.severity == "medium"]) == 0
    return QualityCheckResult(task_id=task.id, issues=issues, passed=passed)
