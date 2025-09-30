# services/comment_service.py

from typing import List, Optional
import uuid
from sqlmodel import Session, select
from fastapi import HTTPException, logger
from datetime import datetime
from services.comment_service.main import Comment, CommentCreate, CommentRead

def create_comment_logic(comment_data: dict, session: Session) -> Comment:
    """Create a new comment."""
    comment_id = f"C-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"
    comment = Comment(id=comment_id, **comment_data)

    session.add(comment)
    session.commit()
    session.refresh(comment)

    return comment

def list_comments_logic(
    session: Session,
    tenant_id: str,
    task_id: str | None = None,
    assignment_id: str | None = None,
    author_id: str | None = None,
    comment_type: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Comment]:
    """Retrieve comments based on filters."""
    query = select(Comment).where(Comment.tenant_id == tenant_id)

    if task_id:
        query = query.where(Comment.task_id == task_id)
    if assignment_id:
        query = query.where(Comment.assignment_id == assignment_id)
    if author_id:
        query = query.where(Comment.author_id == author_id)
    if comment_type:
        query = query.where(Comment.comment_type == comment_type)

    query = query.order_by(Comment.created_at.desc()).offset(skip).limit(limit)
    return session.exec(query).all()

def get_comment_logic(comment_id: str, session: Session) -> Comment:
    """Get a single comment."""
    comment = session.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    return comment

def update_comment_logic(comment_id: str, update_data: dict, session: Session) -> Comment:
    """Update a comment."""
    comment = session.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    for field, value in update_data.items():
        setattr(comment, field, value)

    comment.updated_at = datetime.utcnow()
    session.add(comment)
    session.commit()
    session.refresh(comment)
    return comment

def delete_comment_logic(comment_id: str, session: Session) -> dict:
    """Delete a comment."""
    comment = session.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    session.delete(comment)
    session.commit()
    return {"message": "Comment deleted successfully"}

def get_task_comments_logic(
    session: Session,
    task_id: str,
    tenant_id: str,
    comment_type: Optional[str] = None,
    visibility: Optional[str] = None
) -> List[Comment]:
    """Return all comments for a specific task with optional filters."""
    query = select(Comment).where(
        Comment.task_id == task_id,
        Comment.tenant_id == tenant_id
    )

    if comment_type:
        query = query.where(Comment.comment_type == comment_type)
    if visibility:
        query = query.where(Comment.visibility == visibility)

    query = query.order_by(Comment.created_at.asc())
    comments = session.exec(query).all()
    
    return comments

def create_task_comment_logic(task_id: str, comment_data: CommentCreate, session: Session) -> CommentRead:
    """Business logic to create a comment for a specific task."""
    comment_data.task_id = task_id
    return create_comment_logic(comment_data, session)  # reuse your existing create_comment_logic


def get_assignment_comments_logic(assignment_id: str, tenant_id: str, session: Session) -> list[CommentRead]:
    """Business logic to fetch all comments for a specific assignment."""
    query = (
        select(Comment)
        .where(Comment.assignment_id == assignment_id, Comment.tenant_id == tenant_id)
        .order_by(Comment.created_at.asc())
    )
    comments = session.exec(query).all()
    logger.info(f"Retrieved {len(comments)} comments for assignment {assignment_id}")
    return comments


def get_comment_thread_logic(comment_id: str, session: Session) -> list[CommentRead]:
    """Business logic to fetch all comments for the same task (thread)."""
    comment = session.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    query = (
        select(Comment)
        .where(Comment.task_id == comment.task_id, Comment.tenant_id == comment.tenant_id)
        .order_by(Comment.created_at.asc())
    )
    comments = session.exec(query).all()
    logger.info(f"Retrieved thread of {len(comments)} comments for task {comment.task_id}")
    return comments

def create_status_update_logic(
    task_id: str,
    status: str,
    note: str,
    tenant_id: str,
    session: Session
) -> CommentRead:
    """Business logic to create a status update comment."""
    comment_data = CommentCreate(
        task_id=task_id,
        content=f"Status updated to '{status}': {note}",
        tenant_id=tenant_id,
        comment_type="status_update",
        visibility="all",
        priority="normal"
    )

    return create_comment_logic(comment_data, session)

# Match function to return logic function and path variables
def match_comment_func(method: str, path: str):
    method = method.upper()
    parts = path.strip("/").split("/")

    # Top-level comments
    if method == "GET" and path == "comments":
        return list_comments_logic, {}
    if method == "POST" and path == "comments":
        return create_comment_logic, {}

    # Single comment
    if len(parts) == 2 and parts[0] == "comments":
        comment_id = parts[1]
        if method == "GET":
            return get_comment_logic, {"comment_id": comment_id}
        if method == "PUT":
            return update_comment_logic, {"comment_id": comment_id}
        if method == "DELETE":
            return delete_comment_logic, {"comment_id": comment_id}

    # Task comments
    if len(parts) == 3 and parts[0] == "tasks" and parts[2] == "comments":
        task_id = parts[1]
        if method == "GET":
            return get_task_comments_logic, {"task_id": task_id}
        if method == "POST":
            return create_task_comment_logic, {"task_id": task_id}

    # Task status update
    if len(parts) == 3 and parts[0] == "tasks" and parts[2] == "status-update":
        return create_status_update_logic, {"task_id": parts[1]}

    # Assignment comments
    if len(parts) == 3 and parts[0] == "assignments" and parts[2] == "comments":
        return get_assignment_comments_logic, {"assignment_id": parts[1]}

    # Comment thread
    if len(parts) == 3 and parts[0] == "comments" and parts[2] == "thread":
        return get_comment_thread_logic, {"comment_id": parts[1]}

    return None, {}

# Function map — maps names to the actual logic functions
comment_func_map = {
    "list_comments": list_comments_logic,
    "create_comment": create_comment_logic,
    "get_comment": get_comment_logic,
    "update_comment": update_comment_logic,
    "delete_comment": delete_comment_logic,
    "get_task_comments": get_task_comments_logic,
    "create_task_comment": create_task_comment_logic,
    "get_assignment_comments": get_assignment_comments_logic,
    "get_comment_thread": get_comment_thread_logic,
    "create_status_update": create_status_update_logic,
}
