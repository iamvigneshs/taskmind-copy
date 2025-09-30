# Copyright (c) 2025 Acarin Inc. All rights reserved.
# Proprietary and confidential.
"""API Gateway - Orchestrates microservices for MissionMind TasksMind."""

import os
import httpx
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging

from app.database import get_session
from assignment_service import create_assignment_logic, list_approvals_logic, list_assignments_logic
from task_service import TASK_FUNCTION_MAP, create_task_logic, get_task_logic, match_path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment configuration
GATEWAY_PORT = int(os.getenv("GATEWAY_PORT", "8000"))

# Service URLs
# TASK_SERVICE_URL = os.getenv("TASK_SERVICE_URL", "http://localhost:8001")
# USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://localhost:8002")
# TENANT_SERVICE_URL = os.getenv("TENANT_SERVICE_URL", "http://localhost:8003")
# ASSIGNMENT_SERVICE_URL = os.getenv("ASSIGNMENT_SERVICE_URL", "http://localhost:8004")
COMMENT_SERVICE_URL = os.getenv("COMMENT_SERVICE_URL", "http://localhost:8005")
# AUTHORITY_SERVICE_URL = os.getenv("AUTHORITY_SERVICE_URL", "http://localhost:8006")

# FastAPI application
app = FastAPI(
    title="MissionMind TasksMind API Gateway",
    description="API Gateway for task orchestration microservices",
    version="2.0.0"
)

session = get_session()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service discovery and health checking
services = {
    # "task-service": TASK_SERVICE_URL,
    # "user-service": USER_SERVICE_URL,
    # "tenant-service": TENANT_SERVICE_URL,
    # "assignment-service": ASSIGNMENT_SERVICE_URL,
    "comment-service": COMMENT_SERVICE_URL,
    # "authority-service": AUTHORITY_SERVICE_URL,
}

# API Models for orchestrated workflows
class TaskWorkflowCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    due_date: Optional[datetime] = None
    assigned_to: Optional[str] = None
    tenant_id: str
    org_unit_id: Optional[str] = None

class TaskWorkflowRead(BaseModel):
    task: Dict[str, Any]
    assignment: Optional[Dict[str, Any]] = None
    comments: List[Dict[str, Any]] = []
    approvals: List[Dict[str, Any]] = []

class AssignmentWorkflow(BaseModel):
    task_id: str
    assigned_to: str
    tenant_id: str
    note: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: str = "medium"

class ApprovalWorkflow(BaseModel):
    task_id: str
    assignment_id: str
    approved: bool
    approval_note: Optional[str] = None
    tenant_id: str

class CommentWorkflow(BaseModel):
    task_id: str
    content: str
    tenant_id: str
    comment_type: str = "general"

# Helper functions
async def call_service(service_url: str, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None):
    """Make HTTP calls to microservices."""
    url = f"{service_url}{endpoint}"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            if method.upper() == "GET":
                response = await client.get(url, params=params)
            elif method.upper() == "POST":
                response = await client.post(url, json=data, params=params)
            elif method.upper() == "PUT":
                response = await client.put(url, json=data, params=params)
            elif method.upper() == "DELETE":
                response = await client.delete(url, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            return response
        except httpx.RequestError as e:
            logger.error(f"Service call failed: {url} - {str(e)}")
            raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")

async def check_service_health(service_name: str, service_url: str) -> bool:
    """Check if a service is healthy."""
    try:
        response = await call_service(service_url, "GET", "/health")
        return response.status_code == 200
    except:
        return False

# Health and status endpoints
@app.get("/health")
async def gateway_health():
    """Gateway health check."""
    service_health = {}
    overall_healthy = True
    
    for service_name, service_url in services.items():
        is_healthy = await check_service_health(service_name, service_url)
        service_health[service_name] = "healthy" if is_healthy else "unhealthy"
        if not is_healthy:
            overall_healthy = False
    
    status = "healthy" if overall_healthy else "degraded"
    
    return {
        "status": status,
        "gateway": "healthy",
        "services": service_health,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/")
def root():
    """Root endpoint."""
    return {
        "service": "MissionMind TasksMind API Gateway",
        "version": "2.0.0",
        "description": "Microservices orchestration for task management",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "tasks": "/api/v2/tasks",
            "assignments": "/api/v2/assignments", 
            "comments": "/api/v2/comments",
            "workflows": "/api/v2/workflows"
        }
    }

# Orchestrated workflow endpoints
@app.post("/api/v2/workflows/tasks", response_model=TaskWorkflowRead)
async def create_task_workflow(workflow_data: TaskWorkflowCreate):
    """Create a complete task workflow: task + optional assignment."""
    # Step 1: Create the task
    task_data = {
        "title": workflow_data.title,
        "description": workflow_data.description,
        "priority": workflow_data.priority,
        "due_date": workflow_data.due_date.isoformat() if workflow_data.due_date else None,
        "tenant_id": workflow_data.tenant_id,
        "org_unit_id": workflow_data.org_unit_id
    }
    
    task_response = create_task_logic(task_data.dict(), session)
    if task_response.status_code != 200:
        raise HTTPException(status_code=task_response.status_code, detail="Failed to create task")
    
    task = task_response.json()
    result = TaskWorkflowRead(task=task, comments=[], approvals=[])
    
    # Step 2: Create assignment if specified
    if workflow_data.assigned_to:
        assignment_data = {
            "task_id": task["id"],
            "assigned_to": workflow_data.assigned_to,
            "tenant_id": workflow_data.tenant_id,
            "due_date": workflow_data.due_date.isoformat() if workflow_data.due_date else None,
            "priority": workflow_data.priority,
            "note": f"Auto-assigned during task creation"
        }
        
        assignment_response = create_assignment_logic(assignment_data, session)
        if assignment_response.status_code == 200:
            result.assignment = assignment_response.json()
            
            # Step 3: Create initial comment
            comment_data = {
                "task_id": task["id"],
                "content": f"Task created and assigned to {workflow_data.assigned_to}",
                "tenant_id": workflow_data.tenant_id,
                "comment_type": "status_update"
            }
            
            comment_response = await call_service(COMMENT_SERVICE_URL, "POST", "/comments", comment_data)
            if comment_response.status_code == 200:
                result.comments.append(comment_response.json())
    
    logger.info(f"Created task workflow: {task['id']}")
    return result

@app.get("/api/v2/workflows/tasks/{task_id}", response_model=TaskWorkflowRead)
async def get_task_workflow(task_id: str, tenant_id: str):
    """Get complete task workflow with all related data."""
    # Get task
    task_response = get_task_logic(task_id, session)
    if task_response.status_code != 200:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = task_response.json()
    
    # Get assignments
    assignments = list_assignments_logic(
    session=session,
    tenant_id=tenant_id,
    assigned_to=None,   # optional filter if needed
    status=None,        # optional filter if needed
    skip=0,
    limit=100
)
    
    # Get comments
    comments_response = await call_service(
        COMMENT_SERVICE_URL, "GET", f"/tasks/{task_id}/comments",
        params={"tenant_id": tenant_id}
    )
    comments = comments_response.json() if comments_response.status_code == 200 else []
    
    # Get approvals
    approvals = list_approvals_logic(session=session, tenant_id=tenant_id, task_id=task_id)
    
    return TaskWorkflowRead(
        task=task,
        assignment=assignments[0] if assignments else None,
        comments=comments,
        approvals=approvals
    )

@app.post("/api/v2/workflows/assign")
async def assign_task_workflow(workflow_data: AssignmentWorkflow):
    """Assign a task with comment tracking."""
    # Create assignment
    assignment_dict = workflow_data.model_dump()
    try:
     assignment = create_assignment_logic(assignment_dict, session)
    except HTTPException as e:
    # If your logic function raises HTTPException for errors
      raise HTTPException(status_code=e.status_code, detail=e.detail)
    
    # Create assignment comment
    comment_data = {
        "task_id": workflow_data.task_id,
        "content": f"Task assigned to {workflow_data.assigned_to}. Note: {workflow_data.note or 'No additional notes'}",
        "tenant_id": workflow_data.tenant_id,
        "comment_type": "status_update",
        "assignment_id": assignment["id"]
    }
    
    await call_service(COMMENT_SERVICE_URL, "POST", "/comments", comment_data)
    
    logger.info(f"Assigned task {workflow_data.task_id} to {workflow_data.assigned_to}")
    return assignment

@app.post("/api/v2/workflows/approve")
async def approve_task_workflow(workflow_data: ApprovalWorkflow):
    """Approve/reject a task with comment tracking."""
    # Create approval
    approval_data = {
        "task_id": workflow_data.task_id,
        "assignment_id": workflow_data.assignment_id,
        "tenant_id": workflow_data.tenant_id
    }
    
    approval_response = await call_service(ASSIGNMENT_SERVICE_URL, "POST", "/approvals", approval_data)
    if approval_response.status_code != 200:
        raise HTTPException(status_code=approval_response.status_code, detail="Failed to create approval")
    
    approval = approval_response.json()
    
    # Update approval status
    update_data = {
        "status": "approved" if workflow_data.approved else "rejected",
        "approval_note": workflow_data.approval_note
    }
    
    update_response = await call_service(
        ASSIGNMENT_SERVICE_URL, "PUT", f"/approvals/{approval['id']}", update_data
    )
    
    # Create approval comment
    status_text = "approved" if workflow_data.approved else "rejected"
    comment_data = {
        "task_id": workflow_data.task_id,
        "content": f"Task {status_text}. Note: {workflow_data.approval_note or 'No additional notes'}",
        "tenant_id": workflow_data.tenant_id,
        "comment_type": "approval_note"
    }
    
    await call_service(COMMENT_SERVICE_URL, "POST", "/comments", comment_data)
    
    logger.info(f"Task {workflow_data.task_id} {status_text}")
    return update_response.json() if update_response.status_code == 200 else approval

@app.post("/api/v2/workflows/comment")
async def add_comment_workflow(workflow_data: CommentWorkflow):
    """Add a comment to a task."""
    comment_response = await call_service(COMMENT_SERVICE_URL, "POST", "/comments", workflow_data.model_dump())
    if comment_response.status_code != 200:
        raise HTTPException(status_code=comment_response.status_code, detail="Failed to create comment")
    
    logger.info(f"Added comment to task {workflow_data.task_id}")
    return comment_response.json()

# Direct service proxy endpoints
# @app.api_route("/api/v2/tasks/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
# async def proxy_task_service(request: Request, path: str):
#     """Proxy requests to Task Service."""
#     method = request.method
#     query_params = dict(request.query_params)
    
#     if method in ["POST", "PUT"]:
#         body = await request.json() if request.headers.get("content-type") == "application/json" else None
#         response = await call_service(TASK_SERVICE_URL, method, f"/{path}", body, query_params)
#     else:
#         response = await call_service(TASK_SERVICE_URL, method, f"/{path}", params=query_params)
    
#     return JSONResponse(content=response.json(), status_code=response.status_code)

@app.api_route("/api/v2/tasks/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_task_service(request: Request, path: str, session ):
    method = request.method
    query_params = dict(request.query_params)
    
    # 1️⃣ Match the path to a function and extract variables
    route_key, path_vars = match_path(path)
    
    # 2️⃣ Find the function based on method
    func_map = TASK_FUNCTION_MAP.get(route_key)
    if not func_map or method not in func_map:
        raise HTTPException(status_code=404, detail="Method not allowed")
    
    func = func_map[method]
    
    # 3️⃣ Prepare input arguments
    if method in ["POST", "PUT"]:
        body = await request.json() if request.headers.get("content-type") == "application/json" else {}
        # Merge path variables and body for the function
        result = func(**path_vars, update_data=body, session=session) if method == "PUT" else func(body, session)
    elif method == "GET":
        result = func(**path_vars, session=session, **query_params)  # For GET list or get task
    elif method == "DELETE":
        result = func(**path_vars, session=session)
    else:
        raise HTTPException(status_code=405, detail="Method not allowed")
    
    # 4️⃣ Return response
    return JSONResponse(content=result if isinstance(result, dict) else result.__dict__)

@app.api_route("/api/v2/assignments/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_assignment_service(request: Request, path: str):
    """Proxy requests to Assignment Service."""
    method = request.method
    query_params = dict(request.query_params)
    
    if method in ["POST", "PUT"]:
        body = await request.json() if request.headers.get("content-type") == "application/json" else None
        response = await call_service(ASSIGNMENT_SERVICE_URL, method, f"/{path}", body, query_params)
    else:
        response = await call_service(ASSIGNMENT_SERVICE_URL, method, f"/{path}", params=query_params)
    
    return JSONResponse(content=response.json(), status_code=response.status_code)

@app.api_route("/api/v2/comments/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_comment_service(request: Request, path: str):
    """Proxy requests to Comment Service."""
    method = request.method
    query_params = dict(request.query_params)
    
    if method in ["POST", "PUT"]:
        body = await request.json() if request.headers.get("content-type") == "application/json" else None
        response = await call_service(COMMENT_SERVICE_URL, method, f"/{path}", body, query_params)
    else:
        response = await call_service(COMMENT_SERVICE_URL, method, f"/{path}", params=query_params)
    
    return JSONResponse(content=response.json(), status_code=response.status_code)

# User dashboard endpoint
@app.get("/api/v2/dashboard/{user_id}")
async def get_user_dashboard(user_id: str, tenant_id: str):
    """Get user dashboard with assigned tasks, pending approvals, and recent comments."""
    # Get assigned tasks
    assigned_tasks_response = await call_service(
        ASSIGNMENT_SERVICE_URL, "GET", "/assignments",
        params={"tenant_id": tenant_id, "assigned_to": user_id, "status": "pending"}
    )
    assigned_tasks = assigned_tasks_response.json() if assigned_tasks_response.status_code == 200 else []
    
    # Get pending approvals
    pending_approvals_response = await call_service(
        ASSIGNMENT_SERVICE_URL, "GET", "/approvals",
        params={"tenant_id": tenant_id, "approver_id": user_id, "status": "pending"}
    )
    pending_approvals = pending_approvals_response.json() if pending_approvals_response.status_code == 200 else []
    
    # Get recent comments by user
    recent_comments_response = await call_service(
        COMMENT_SERVICE_URL, "GET", "/comments",
        params={"tenant_id": tenant_id, "author_id": user_id, "limit": 10}
    )
    recent_comments = recent_comments_response.json() if recent_comments_response.status_code == 200 else []
    
    return {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "assigned_tasks": assigned_tasks,
        "pending_approvals": pending_approvals,
        "recent_comments": recent_comments,
        "summary": {
            "total_assigned": len(assigned_tasks),
            "pending_approvals": len(pending_approvals),
            "recent_activity": len(recent_comments)
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=GATEWAY_PORT)