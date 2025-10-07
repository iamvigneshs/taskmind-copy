# task_service.py
from typing import List, Optional
import uuid
from datetime import datetime

from fastapi import HTTPException
from services.task_service.main import Task
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)



priority_scores = {"low": 0.3, "medium": 0.5, "high": 0.8}

def create_task_logic(task_data: dict, session: Session) -> Task:
    """Business logic for creating a task (can be reused anywhere)."""
    task_id = f"T-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"
    
    priority_score = priority_scores.get(task_data.get("priority", "medium"), 0.5)
    
    task = Task(
        id=task_id,
        title=task_data["title"],
        description=task_data.get("description"),
        priority=task_data.get("priority"),
        due_date=task_data.get("due_date"),
        tenant_id=task_data.get("tenant_id"),
        org_unit_id=task_data.get("org_unit_id"),
        priority_score=priority_score,
        created_by="system",
        approved_by = task_data.get("approved_by")
    )
    
    session.add(task)
    session.commit()
    session.refresh(task)
    
    logger.info(f"Created task {task_id} for tenant {task_data.get('tenant_id')}")
    return task

def get_task_logic(task_id: str, session: Session) -> Task:
    """Business logic to retrieve a single task by ID."""
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    logger.info(f"Retrieved task {task_id} for tenant {task.tenant_id}")
    return task

def update_task_logic(task_id: str, update_data: dict, session: Session) -> Task:
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    for field, value in update_data.items():
        setattr(task, field, value)
    task.updated_at = datetime.utcnow()
    if "priority" in update_data:
        task.priority_score = priority_scores.get(task.priority, 0.5)
    session.add(task)
    session.commit()
    session.refresh(task)
    return task

def delete_task_logic(task_id: str, session: Session):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    session.delete(task)
    session.commit()
    return {"message": "Task deleted successfully"}

def assign_task_logic(task_id: str, assigned_to: str, session: Session) -> Task:
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.assigned_to = assigned_to
    task.status = "assigned"
    task.updated_at = datetime.utcnow()
    session.add(task)
    session.commit()
    session.refresh(task)
    return task

def complete_task_logic(task_id: str, session: Session) -> Task:
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.status = "completed"
    task.updated_at = datetime.utcnow()
    session.add(task)
    session.commit()
    session.refresh(task)
    return task

def list_tasks_logic(
    session: Session,
    tenant_id: str,
    status: Optional[str] = None,
    assigned_to: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Task]:
    """Business logic to list tasks with filters."""
    query = session.query(Task).filter(Task.tenant_id == tenant_id)
    
    if status:
        query = query.filter(Task.status == status)
    if assigned_to:
        query = query.filter(Task.assigned_to == assigned_to)
    
    tasks = query.offset(skip).limit(limit).all()
    
    logger.info(f"Retrieved {len(tasks)} tasks for tenant {tenant_id}")
    return tasks

TASK_FUNCTION_MAP = {
    "tasks": { "POST": create_task_logic, "GET": list_tasks_logic },
    "tasks/{task_id}": { "GET": get_task_logic, "PUT": update_task_logic, "DELETE": delete_task_logic },
    "tasks/{task_id}/assign": { "POST": assign_task_logic },
    "tasks/{task_id}/complete": { "POST": complete_task_logic },
}

def match_path(path: str):
    """Match dynamic path like 'tasks/123/assign' to a key in TASK_FUNCTION_MAP and extract variables"""
    parts = path.strip("/").split("/")
    
    if len(parts) == 1 and parts[0] == "tasks":
        return "tasks", {}
    
    if len(parts) == 2 and parts[0] == "tasks":
        return "tasks/{task_id}", {"task_id": parts[1]}
    
    if len(parts) == 3 and parts[0] == "tasks" and parts[2] == "assign":
        return "tasks/{task_id}/assign", {"task_id": parts[1]}
    
    if len(parts) == 3 and parts[0] == "tasks" and parts[2] == "complete":
        return "tasks/{task_id}/complete", {"task_id": parts[1]}
    
    raise HTTPException(status_code=404, detail="Endpoint not found")
