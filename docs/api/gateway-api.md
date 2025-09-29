# API Gateway Documentation

**Base URL**: `https://api.tasksmind.com` (Production) | `http://localhost:8000` (Development)  
**API Version**: v2  
**Authentication**: Bearer JWT (Future) | None (Current)  
**Content-Type**: `application/json`

## 🚀 Quick Start

### **Health Check**
```bash
curl -X GET "http://localhost:8000/health"
```

### **API Information**
```bash
curl -X GET "http://localhost:8000/api/v2/info"
```

### **Interactive Documentation**
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🏗️ API Architecture

### **Request Flow**
```
Client → API Gateway → Microservice → Database → Response
```

### **Orchestrated vs Direct APIs**
- **Orchestrated**: `/api/v2/workflows/*` - Multi-service coordination
- **Direct**: `/api/v2/tasks/*` - Single service access

## 📋 Orchestrated Workflow APIs

### **1. Complete Task Workflow**

#### **Create Task with Assignment**
```http
POST /api/v2/workflows/tasks
Content-Type: application/json

{
  "title": "Security Assessment Q1 2025",
  "description": "Comprehensive security review of network infrastructure",
  "priority": "high",
  "assigned_to": "john.doe",
  "tenant_id": "acme-corp",
  "org_unit_id": "CYBERSEC-DIV",
  "due_date": "2025-12-31T17:00:00Z"
}
```

**Response**:
```json
{
  "task": {
    "id": "T-20250929-a93b50ed",
    "title": "Security Assessment Q1 2025",
    "description": "Comprehensive security review of network infrastructure",
    "priority": "high",
    "status": "pending",
    "created_at": "2025-09-29T19:10:00.667559",
    "updated_at": "2025-09-29T19:10:00.667559",
    "due_date": "2025-12-31T17:00:00",
    "created_by": "system",
    "assigned_to": "john.doe",
    "approved_by": null,
    "tenant_id": "acme-corp",
    "org_unit_id": "CYBERSEC-DIV",
    "priority_score": 0.8
  },
  "assignment": {
    "id": "A-20250929-576cc071",
    "task_id": "T-20250929-a93b50ed",
    "assigned_to": "john.doe",
    "assigned_by": "system",
    "tenant_id": "acme-corp",
    "status": "pending",
    "assigned_at": "2025-09-29T19:10:00.680529",
    "due_date": "2025-12-31T17:00:00",
    "completed_at": null,
    "note": "Auto-assigned during task creation",
    "priority": "high"
  },
  "comments": [
    {
      "id": "C-20250929-f0e8638d",
      "task_id": "T-20250929-a93b50ed",
      "content": "Task created and assigned to john.doe",
      "comment_type": "status_update",
      "created_at": "2025-09-29T19:10:00.698257",
      "author_id": "system",
      "tenant_id": "acme-corp"
    }
  ],
  "approvals": []
}
```

#### **Get Complete Task Workflow**
```http
GET /api/v2/workflows/tasks/{task_id}?tenant_id=acme-corp
```

**Response**: Same structure as create response, with all current data

### **2. Assignment Workflow**

#### **Assign Task to User**
```http
POST /api/v2/workflows/assign
Content-Type: application/json

{
  "task_id": "T-20250929-a93b50ed",
  "assigned_to": "jane.smith",
  "tenant_id": "acme-corp",
  "due_date": "2025-12-15T17:00:00Z",
  "note": "Reassigning to senior analyst for specialized expertise",
  "priority": "high"
}
```

**Response**:
```json
{
  "id": "A-20250929-new456",
  "task_id": "T-20250929-a93b50ed",
  "assigned_to": "jane.smith",
  "assigned_by": "system",
  "tenant_id": "acme-corp",
  "status": "pending",
  "assigned_at": "2025-09-29T20:15:00.123456",
  "due_date": "2025-12-15T17:00:00",
  "note": "Reassigning to senior analyst for specialized expertise",
  "priority": "high"
}
```

### **3. Approval Workflow**

#### **Approve/Reject Task**
```http
POST /api/v2/workflows/approve
Content-Type: application/json

{
  "task_id": "T-20250929-a93b50ed",
  "assignment_id": "A-20250929-576cc071",
  "approved": true,
  "approval_note": "Security assessment completed successfully. All requirements met.",
  "tenant_id": "acme-corp"
}
```

**Response**:
```json
{
  "id": "AP-20250929-918dd4f8",
  "task_id": "T-20250929-a93b50ed",
  "assignment_id": "A-20250929-576cc071",
  "approver_id": "system",
  "tenant_id": "acme-corp",
  "status": "approved",
  "approved_at": "2025-09-29T20:30:00.815608",
  "approval_note": "Security assessment completed successfully. All requirements met.",
  "authority_level": null,
  "requires_additional_approval": false
}
```

### **4. Comment Workflow**

#### **Add Comment to Task**
```http
POST /api/v2/workflows/comment
Content-Type: application/json

{
  "task_id": "T-20250929-a93b50ed",
  "content": "Phase 1 completed: Network discovery identified 45 assets. Moving to vulnerability assessment phase.",
  "tenant_id": "acme-corp",
  "comment_type": "status_update"
}
```

**Response**:
```json
{
  "id": "C-20250929-9f554535",
  "task_id": "T-20250929-a93b50ed",
  "assignment_id": null,
  "author_id": "system",
  "tenant_id": "acme-corp",
  "content": "Phase 1 completed: Network discovery identified 45 assets. Moving to vulnerability assessment phase.",
  "comment_type": "status_update",
  "created_at": "2025-09-29T20:45:00.727796",
  "updated_at": "2025-09-29T20:45:00.727796",
  "is_internal": false,
  "visibility": "all",
  "priority": "normal"
}
```

### **5. User Dashboard**

#### **Get User Dashboard**
```http
GET /api/v2/dashboard/{user_id}?tenant_id=acme-corp
```

**Response**:
```json
{
  "user_id": "john.doe",
  "tenant_id": "acme-corp",
  "assigned_tasks": [
    {
      "id": "A-20250929-576cc071",
      "task_id": "T-20250929-a93b50ed",
      "assigned_to": "john.doe",
      "status": "pending",
      "priority": "high",
      "due_date": "2025-12-31T17:00:00"
    }
  ],
  "pending_approvals": [
    {
      "id": "AP-20250929-pending123",
      "task_id": "T-20250925-other789",
      "status": "pending",
      "assigned_at": "2025-09-25T10:00:00"
    }
  ],
  "recent_comments": [
    {
      "id": "C-20250929-recent456",
      "task_id": "T-20250929-a93b50ed",
      "content": "Latest progress update",
      "created_at": "2025-09-29T20:45:00.727796"
    }
  ],
  "summary": {
    "total_assigned": 3,
    "pending_approvals": 2,
    "recent_activity": 5
  }
}
```

## 🔗 Direct Service APIs

### **Task Service APIs**

#### **Create Task (Direct)**
```http
POST /api/v2/tasks/tasks
Content-Type: application/json

{
  "title": "Direct Task Creation",
  "description": "Creating task directly via task service",
  "priority": "medium",
  "tenant_id": "acme-corp",
  "org_unit_id": "IT-DEPT"
}
```

#### **List Tasks**
```http
GET /api/v2/tasks/tasks?tenant_id=acme-corp&status=pending&limit=50
```

#### **Get Task by ID**
```http
GET /api/v2/tasks/tasks/{task_id}
```

#### **Update Task**
```http
PUT /api/v2/tasks/tasks/{task_id}
Content-Type: application/json

{
  "status": "in_progress",
  "assigned_to": "new.assignee"
}
```

#### **Delete Task**
```http
DELETE /api/v2/tasks/tasks/{task_id}
```

### **Assignment Service APIs**

#### **Create Assignment (Direct)**
```http
POST /api/v2/assignments/assignments
Content-Type: application/json

{
  "task_id": "T-20250929-a93b50ed",
  "assigned_to": "direct.user",
  "tenant_id": "acme-corp",
  "priority": "medium",
  "note": "Direct assignment creation"
}
```

#### **List Assignments**
```http
GET /api/v2/assignments/assignments?tenant_id=acme-corp&assigned_to=john.doe
```

#### **Complete Assignment**
```http
PUT /api/v2/assignments/assignments/{assignment_id}/complete
```

#### **Route Assignment**
```http
POST /api/v2/assignments/assignments/{assignment_id}/route
Content-Type: application/json

{
  "new_assignee": "routing.target",
  "route_note": "Routing to specialist for technical expertise"
}
```

### **Comment Service APIs**

#### **Create Comment (Direct)**
```http
POST /api/v2/comments/comments
Content-Type: application/json

{
  "task_id": "T-20250929-a93b50ed",
  "content": "Direct comment creation",
  "tenant_id": "acme-corp",
  "comment_type": "general",
  "visibility": "all"
}
```

#### **List Comments**
```http
GET /api/v2/comments/comments?tenant_id=acme-corp&task_id=T-20250929-a93b50ed
```

#### **Get Task Comments**
```http
GET /api/v2/comments/tasks/{task_id}/comments?tenant_id=acme-corp
```

#### **Update Comment**
```http
PUT /api/v2/comments/comments/{comment_id}
Content-Type: application/json

{
  "content": "Updated comment content",
  "visibility": "assignees_only"
}
```

## 📝 Data Models

### **Task Model**
```typescript
interface Task {
  id: string;                    // Format: T-YYYYMMDD-xxxxxxxx
  title: string;                 // Max 200 chars
  description?: string;          // Optional long description
  priority: "low" | "medium" | "high";
  status: "pending" | "assigned" | "approved" | "completed" | "rejected";
  created_at: string;           // ISO 8601 datetime
  updated_at: string;           // ISO 8601 datetime
  due_date?: string;            // ISO 8601 datetime
  created_by?: string;          // User ID
  assigned_to?: string;         // User ID
  approved_by?: string;         // User ID
  tenant_id: string;            // Tenant identifier
  org_unit_id?: string;         // Organization unit
  priority_score: number;       // 0.0 - 1.0 calculated score
}
```

### **Assignment Model**
```typescript
interface Assignment {
  id: string;                   // Format: A-YYYYMMDD-xxxxxxxx
  task_id: string;              // Related task ID
  assigned_to: string;          // User ID
  assigned_by: string;          // User ID
  tenant_id: string;            // Tenant identifier
  status: "pending" | "accepted" | "completed" | "rejected";
  assigned_at: string;          // ISO 8601 datetime
  due_date?: string;            // ISO 8601 datetime
  completed_at?: string;        // ISO 8601 datetime
  note?: string;                // Assignment note
  priority: "low" | "medium" | "high";
}
```

### **Comment Model**
```typescript
interface Comment {
  id: string;                   // Format: C-YYYYMMDD-xxxxxxxx
  task_id: string;              // Related task ID
  assignment_id?: string;       // Optional assignment link
  author_id: string;            // User ID
  tenant_id: string;            // Tenant identifier
  content: string;              // Comment content
  comment_type: "general" | "status_update" | "route_note" | "approval_note";
  created_at: string;           // ISO 8601 datetime
  updated_at: string;           // ISO 8601 datetime
  is_internal: boolean;         // Internal vs external
  visibility: "all" | "assignees_only" | "approvers_only";
  priority: "urgent" | "normal" | "low";
}
```

### **Approval Model**
```typescript
interface Approval {
  id: string;                   // Format: AP-YYYYMMDD-xxxxxxxx
  task_id: string;              // Related task ID
  assignment_id: string;        // Related assignment ID
  approver_id: string;          // User ID
  tenant_id: string;            // Tenant identifier
  status: "pending" | "approved" | "rejected";
  approved_at?: string;         // ISO 8601 datetime
  approval_note?: string;       // Approval comment
  authority_level?: string;     // Required authority level
  requires_additional_approval: boolean;
}
```

## ⚠️ Error Handling

### **Standard Error Response**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request data",
    "details": [
      {
        "field": "tenant_id",
        "message": "Field required"
      },
      {
        "field": "title",
        "message": "Ensure this value has at least 2 characters"
      }
    ],
    "timestamp": "2025-09-29T20:00:00.000000",
    "request_id": "req-123456789"
  }
}
```

### **HTTP Status Codes**

| Code | Description | Usage |
|------|-------------|-------|
| 200 | OK | Successful GET, PUT |
| 201 | Created | Successful POST |
| 400 | Bad Request | Invalid input data |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 422 | Unprocessable Entity | Validation errors |
| 500 | Internal Server Error | Server-side error |
| 503 | Service Unavailable | Dependent service down |

### **Error Types**

- **`VALIDATION_ERROR`**: Input validation failed
- **`AUTHENTICATION_ERROR`**: Invalid or missing authentication
- **`AUTHORIZATION_ERROR`**: Insufficient permissions
- **`NOT_FOUND_ERROR`**: Requested resource not found
- **`BUSINESS_LOGIC_ERROR`**: Business rule violation
- **`SERVICE_UNAVAILABLE_ERROR`**: Dependent service unavailable
- **`INTERNAL_SERVER_ERROR`**: Unexpected server error

## 🔐 Authentication & Security

### **Bearer Token Authentication (Future)**
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### **Tenant Context**
All requests must include `tenant_id` for multi-tenant isolation:
```json
{
  "tenant_id": "acme-corp",
  // ... other request data
}
```

### **Rate Limiting (Future)**
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1672531200
```

## 📊 API Metrics & Monitoring

### **Health Endpoints**

#### **System Health**
```http
GET /health
```

**Response**:
```json
{
  "status": "healthy",
  "gateway": "healthy",
  "services": {
    "task-service": "healthy",
    "assignment-service": "healthy", 
    "comment-service": "healthy",
    "user-service": "unhealthy",
    "tenant-service": "unhealthy",
    "authority-service": "unhealthy"
  },
  "timestamp": "2025-09-29T20:00:00.000000"
}
```

#### **Service Metrics**
```http
GET /metrics
```

**Response**:
```json
{
  "service": "api-gateway",
  "version": "2.0.0", 
  "uptime_seconds": 86400,
  "requests_total": 15420,
  "requests_per_minute": 45.2,
  "average_response_time_ms": 180,
  "error_rate_percent": 0.1,
  "timestamp": "2025-09-29T20:00:00.000000"
}
```

## 🧪 API Testing

### **Postman Collection**
```bash
# Import Postman collection
curl -o tasksmind-api.postman_collection.json \
  http://localhost:8000/docs/postman-collection
```

### **OpenAPI Specification**
```bash
# Download OpenAPI spec
curl -o tasksmind-openapi.json \
  http://localhost:8000/openapi.json
```

### **Example Test Script**
```bash
#!/bin/bash
# Complete API test
API_BASE="http://localhost:8000"
TENANT_ID="test-tenant"

# 1. Health check
curl -f "$API_BASE/health" || exit 1

# 2. Create task
TASK=$(curl -s -X POST "$API_BASE/api/v2/workflows/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "API Test Task",
    "tenant_id": "'$TENANT_ID'",
    "assigned_to": "api.tester"
  }')

TASK_ID=$(echo "$TASK" | jq -r '.task.id')
echo "Created task: $TASK_ID"

# 3. Add comment
curl -s -X POST "$API_BASE/api/v2/workflows/comment" \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "'$TASK_ID'",
    "content": "API test comment",
    "tenant_id": "'$TENANT_ID'"
  }' | jq '.content'

echo "API test completed successfully"
```

---

This comprehensive API documentation provides complete reference for integrating with the MissionMind TasksMind microservices platform, supporting military, government, and commercial task orchestration workflows.