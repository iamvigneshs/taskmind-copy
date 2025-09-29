# MissionMind TasksMind - Microservices Deployment Guide

## Overview

This project has been restructured to follow true microservices architecture principles, with each service being independently deployable, scalable, and maintainable.

## Architecture

### Microservices Structure
```
services/
├── task-service/           # Task management and lifecycle
├── assignment-service/     # Task assignments and approvals
├── comment-service/        # Comments and communication
├── api-gateway/           # Request routing and orchestration
├── user-service/          # User management (future)
├── tenant-service/        # Multi-tenant organization management (future)
├── authority-service/     # Authority recommendations (future)
└── common/               # Shared libraries and utilities
```

### Service Communication
- **API Gateway (Port 8000)**: Single entry point for all client requests
- **Task Service (Port 8001)**: Core task management
- **Assignment Service (Port 8004)**: Assignment workflow and approvals
- **Comment Service (Port 8005)**: Communication and notes

### Database Architecture
- **Database per Service**: Each microservice has its own PostgreSQL database
- **No Shared Database Access**: Services communicate only through APIs
- **Event-Driven Updates**: Services synchronize data through HTTP calls

## Development Setup

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- PostgreSQL (for local development)

### Local Development with Docker Compose

1. **Clone and Navigate**
   ```bash
   cd /path/to/tasksmind
   ```

2. **Build and Start All Services**
   ```bash
   docker-compose up --build
   ```

3. **Verify Services**
   ```bash
   # Check all services are healthy
   curl http://localhost:8000/health
   
   # Individual service health checks
   curl http://localhost:8001/health  # Task Service
   curl http://localhost:8004/health  # Assignment Service
   curl http://localhost:8005/health  # Comment Service
   ```

### Individual Service Development

1. **Task Service**
   ```bash
   cd services/task-service
   pip install -r requirements.txt
   export DATABASE_URL="postgresql://taskuser:taskpass123@localhost:5432/tasksmind_tasks"
   python main.py
   ```

2. **Assignment Service**
   ```bash
   cd services/assignment-service
   pip install -r requirements.txt
   export DATABASE_URL="postgresql://assignuser:assignpass123@localhost:5433/tasksmind_assignments"
   export TASK_SERVICE_URL="http://localhost:8001"
   python main.py
   ```

3. **API Gateway**
   ```bash
   cd services/api-gateway
   pip install -r requirements.txt
   export TASK_SERVICE_URL="http://localhost:8001"
   export ASSIGNMENT_SERVICE_URL="http://localhost:8004"
   export COMMENT_SERVICE_URL="http://localhost:8005"
   python main.py
   ```

## Testing the Workflow

### Complete Task Management Workflow

1. **Create a Task with Assignment**
   ```bash
   curl -X POST http://localhost:8000/api/v2/workflows/tasks \
     -H "Content-Type: application/json" \
     -d '{
       "title": "Implement Security Feature",
       "description": "Add two-factor authentication to user login",
       "priority": "high",
       "assigned_to": "john.doe",
       "tenant_id": "acme-corp",
       "org_unit_id": "IT-SECURITY"
     }'
   ```

2. **Get User Dashboard**
   ```bash
   curl "http://localhost:8000/api/v2/dashboard/john.doe?tenant_id=acme-corp"
   ```

3. **Add Comments**
   ```bash
   curl -X POST http://localhost:8000/api/v2/workflows/comment \
     -H "Content-Type: application/json" \
     -d '{
       "task_id": "T-20250929-abc123",
       "content": "Started working on authentication module",
       "tenant_id": "acme-corp",
       "comment_type": "status_update"
     }'
   ```

4. **Approve Task**
   ```bash
   curl -X POST http://localhost:8000/api/v2/workflows/approve \
     -H "Content-Type: application/json" \
     -d '{
       "task_id": "T-20250929-abc123",
       "assignment_id": "A-20250929-def456",
       "approved": true,
       "approval_note": "Approved for implementation",
       "tenant_id": "acme-corp"
     }'
   ```

5. **Get Complete Task Workflow**
   ```bash
   curl "http://localhost:8000/api/v2/workflows/tasks/T-20250929-abc123?tenant_id=acme-corp"
   ```

## Production Deployment

### Kubernetes Deployment

1. **Create Namespace**
   ```bash
   kubectl create namespace tasksmind
   ```

2. **Deploy Database Secrets**
   ```bash
   kubectl create secret generic database-secrets \
     --from-literal=task-db-url="postgresql://user:pass@db-host:5432/tasks" \
     --from-literal=assignment-db-url="postgresql://user:pass@db-host:5432/assignments" \
     --from-literal=comment-db-url="postgresql://user:pass@db-host:5432/comments" \
     -n tasksmind
   ```

3. **Deploy Services**
   ```bash
   kubectl apply -f k8s/deployments/
   ```

4. **Verify Deployment**
   ```bash
   kubectl get pods -n tasksmind
   kubectl get services -n tasksmind
   ```

### Scaling Individual Services

```bash
# Scale Task Service based on load
kubectl scale deployment task-service --replicas=5 -n tasksmind

# Scale Assignment Service
kubectl scale deployment assignment-service --replicas=3 -n tasksmind

# Auto-scaling is configured via HPA in deployment files
```

### Monitoring and Observability

1. **Access Prometheus**
   - URL: http://localhost:9090
   - Metrics from all services available

2. **Access Grafana**
   - URL: http://localhost:3000
   - Username: admin, Password: admin123

3. **Service Health Monitoring**
   ```bash
   # Check overall system health
   curl http://localhost:8000/health
   
   # Individual service metrics
   curl http://localhost:8001/metrics
   curl http://localhost:8004/metrics
   curl http://localhost:8005/metrics
   ```

## Configuration

### Environment Variables

**Task Service:**
- `DATABASE_URL`: PostgreSQL connection string
- `SERVICE_PORT`: Service port (default: 8001)

**Assignment Service:**
- `DATABASE_URL`: PostgreSQL connection string
- `SERVICE_PORT`: Service port (default: 8004)
- `TASK_SERVICE_URL`: Task service endpoint
- `USER_SERVICE_URL`: User service endpoint

**Comment Service:**
- `DATABASE_URL`: PostgreSQL connection string
- `SERVICE_PORT`: Service port (default: 8005)

**API Gateway:**
- `GATEWAY_PORT`: Gateway port (default: 8000)
- `TASK_SERVICE_URL`: Task service endpoint
- `ASSIGNMENT_SERVICE_URL`: Assignment service endpoint
- `COMMENT_SERVICE_URL`: Comment service endpoint

## API Documentation

### Orchestrated Workflows (via API Gateway)

- **POST** `/api/v2/workflows/tasks` - Create task with optional assignment
- **GET** `/api/v2/workflows/tasks/{task_id}` - Get complete task workflow
- **POST** `/api/v2/workflows/assign` - Assign task to user
- **POST** `/api/v2/workflows/approve` - Approve/reject task
- **POST** `/api/v2/workflows/comment` - Add comment to task
- **GET** `/api/v2/dashboard/{user_id}` - Get user dashboard

### Direct Service APIs

- **Task Service**: `/api/v2/tasks/*` - Direct task operations
- **Assignment Service**: `/api/v2/assignments/*` - Direct assignment operations
- **Comment Service**: `/api/v2/comments/*` - Direct comment operations

### Interactive Documentation
- API Gateway: http://localhost:8000/docs
- Task Service: http://localhost:8001/docs
- Assignment Service: http://localhost:8004/docs
- Comment Service: http://localhost:8005/docs

## Microservice Characteristics Implemented

### ✅ Single Responsibility
- Each service manages one business domain
- Clear service boundaries
- Independent data models

### ✅ Database Per Service
- Task Service: `tasksmind_tasks`
- Assignment Service: `tasksmind_assignments`
- Comment Service: `tasksmind_comments`

### ✅ Independent Deployment
- Individual Dockerfiles for each service
- Separate CI/CD pipelines possible
- Kubernetes deployments per service

### ✅ Decentralized Data Management
- No shared databases
- Service-to-service communication via HTTP APIs
- Event-driven updates

### ✅ Fault Tolerance
- Circuit breaker pattern in API Gateway
- Health checks and monitoring
- Graceful degradation

### ✅ Independent Scaling
- Horizontal pod autoscaling configured
- Services can scale independently based on load
- Resource limits and requests defined

### ✅ Technology Diversity
- Each service can use different tech stack
- Common Python/FastAPI for consistency
- Future services can use different languages

## Security Considerations

- **Service-to-Service Authentication**: JWT tokens (future implementation)
- **Network Security**: Services communicate within private network
- **Database Security**: Separate credentials per service
- **Secret Management**: Kubernetes secrets for sensitive data

## Future Enhancements

1. **User Service**: Authentication and user management
2. **Tenant Service**: Multi-tenant organization management
3. **Authority Service**: Authority recommendations and compliance
4. **Message Queue**: Async communication between services
5. **Event Sourcing**: Event-driven architecture implementation
6. **API Versioning**: Support for multiple API versions
7. **Rate Limiting**: Per-service rate limiting
8. **Distributed Tracing**: Full request tracing across services