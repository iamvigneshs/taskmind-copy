from datetime import datetime
from typing import Callable, Optional
from fastapi import HTTPException
from sqlmodel import Session, select
from services.assignment_service.main import Assignment, Approval
from services.task_service.task_service import get_task_logic, update_task_logic
import logging
import uuid

logger = logging.getLogger(__name__)

# -------------------- Assignment Logic --------------------

def create_assignment_logic(assignment_data: dict, session: Session) -> Assignment:
    assignment_id = f"A-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"

    # Verify task exists
    try:
        task = get_task_logic(assignment_data["task_id"], session)
    except HTTPException:
        raise HTTPException(status_code=404, detail="Task not found")

    assignment = Assignment(
        id=assignment_id,
        task_id=assignment_data["task_id"],
        assigned_to=assignment_data["assigned_to"],
        assigned_by="system",
        tenant_id=assignment_data["tenant_id"],
        due_date=assignment_data.get("due_date"),
        note=assignment_data.get("note"),
        priority=assignment_data.get("priority"),
    )

    session.add(assignment)
    session.commit()
    session.refresh(assignment)

    # Update task status
    update_data = {"assigned_to": assignment_data["assigned_to"], "status": "assigned"}
    try:
        update_task_logic(assignment_data["task_id"], update_data, session)
    except HTTPException:
        logger.warning("Could not update task status in Task Service")

    logger.info(f"Created assignment {assignment_id} for task {assignment_data['task_id']}")
    return assignment


def list_assignments_logic(
    session: Session,
    tenant_id: str,
    assigned_to: str = None,
    status: str = None,
    skip: int = 0,
    limit: int = 100,
):
    query = select(Assignment).where(Assignment.tenant_id == tenant_id)
    if assigned_to:
        query = query.where(Assignment.assigned_to == assigned_to)
    if status:
        query = query.where(Assignment.status == status)
    query = query.offset(skip).limit(limit)
    assignments = session.exec(query).all()
    logger.info(f"Retrieved {len(assignments)} assignments for tenant {tenant_id}")
    return assignments


def get_assignment_logic(assignment_id: str, session: Session) -> Assignment:
    assignment = session.get(Assignment, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment


def complete_assignment_logic(assignment_id: str, session: Session) -> Assignment:
    assignment = session.get(Assignment, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    assignment.status = "completed"
    assignment.completed_at = datetime.utcnow()
    session.add(assignment)
    session.commit()
    session.refresh(assignment)

    update_data = {"status": "completed"}
    try:
        update_task_logic(assignment.task_id, update_data, session)
    except HTTPException:
        logger.warning("Could not update task status in Task Service")

    logger.info(f"Completed assignment {assignment_id}")
    return assignment


def route_assignment_logic(assignment_id: str, new_assignee: str, route_note: str, session: Session) -> Assignment:
    assignment = session.get(Assignment, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Create new assignment
    new_assignment_id = f"A-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"
    new_assignment = Assignment(
        id=new_assignment_id,
        task_id=assignment.task_id,
        assigned_to=new_assignee,
        assigned_by=assignment.assigned_to,
        tenant_id=assignment.tenant_id,
        due_date=assignment.due_date,
        note=f"Routed from {assignment.assigned_to}: {route_note or 'No note'}",
        priority=assignment.priority,
    )

    # Complete old assignment
    assignment.status = "completed"
    assignment.completed_at = datetime.utcnow()

    session.add(assignment)
    session.add(new_assignment)
    session.commit()
    session.refresh(new_assignment)

    # Update task assignment
    update_data = {"assigned_to": new_assignee}
    try:
        update_task_logic(assignment.task_id, update_data, session)
    except HTTPException:
        logger.warning("Could not update task assignment in Task Service")

    logger.info(f"Routed assignment {assignment_id} to new assignment {new_assignment_id}")
    return new_assignment

# -------------------- Approval Logic --------------------

def create_approval_logic(approval_data: dict, session: Session) -> Approval:
    approval_id = f"AP-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"
    approval = Approval(
        id=approval_id,
        task_id=approval_data["task_id"],
        assignment_id=approval_data["assignment_id"],
        approver_id="system",
        tenant_id=approval_data["tenant_id"],
        authority_level=approval_data["authority_level"],
    )
    session.add(approval)
    session.commit()
    session.refresh(approval)
    logger.info(f"Created approval {approval_id} for task {approval_data['task_id']}")
    return approval


def list_approvals_logic(session: Session, tenant_id: str, task_id: Optional[str] = None,
                         approver_id: Optional[str] = None, status: Optional[str] = None,
                         skip: int = 0, limit: int = 100):
    query = select(Approval).where(Approval.tenant_id == tenant_id)
    
    if task_id:
        query = query.where(Approval.task_id == task_id)
    if approver_id:
        query = query.where(Approval.approver_id == approver_id)
    if status:
        query = query.where(Approval.status == status)
    
    query = query.offset(skip).limit(limit)
    return session.exec(query).all()


def update_approval_logic(approval_id: str, update_data: dict, session: Session) -> Approval:
    approval = session.get(Approval, approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")

    for field, value in update_data.items():
        setattr(approval, field, value)
    approval.approved_at = datetime.utcnow()
    session.add(approval)
    session.commit()
    session.refresh(approval)

    # Update task status
    new_task_status = "approved" if update_data.get("status") == "approved" else "rejected"
    try:
        update_task_logic(approval.task_id, {"status": new_task_status}, session)
    except HTTPException:
        logger.warning("Could not update task status in Task Service")

    logger.info(f"Updated approval {approval_id} to {update_data.get('status')}")
    return approval


def match_assignment_path(path: str):
    """
    Match dynamic paths like 'assignments/123/route' to keys in TASK_FUNCTION_MAP
    and extract path variables.
    """
    parts = path.strip("/").split("/")

    # Assignments
    if len(parts) == 1 and parts[0] == "assignments":
        return "assignments", {}
    if len(parts) == 2 and parts[0] == "assignments":
        return "assignments/{assignment_id}", {"assignment_id": parts[1]}
    if len(parts) == 3 and parts[0] == "assignments" and parts[2] == "complete":
        return "assignments/{assignment_id}/complete", {"assignment_id": parts[1]}
    if len(parts) == 3 and parts[0] == "assignments" and parts[2] == "route":
        return "assignments/{assignment_id}/route", {"assignment_id": parts[1]}

    # Approvals
    if len(parts) == 1 and parts[0] == "approvals":
        return "approvals", {}
    if len(parts) == 2 and parts[0] == "approvals":
        return "approvals/{approval_id}", {"approval_id": parts[1]}

    raise HTTPException(status_code=404, detail=f"Endpoint '{path}' not found")


TASK_ASSIGN_FUNCTION_MAP: dict[str, Callable] = {
    # Assignments
    "assignments": list_assignments_logic,
    "assignments/create": create_assignment_logic,
    "assignments/get": get_assignment_logic,
    "assignments/complete": complete_assignment_logic,
    "assignments/route": route_assignment_logic,
    # Approvals
    "approvals": list_approvals_logic,
    "approvals/create": create_approval_logic,
    "approvals/update": update_approval_logic
}