# MissionMind TasksMind - Microservices Architecture

This directory contains the microservices for the MissionMind TasksMind platform, designed for military, government, and commercial task orchestration.

## Microservices Overview

### Core Services

1. **Task Service** (`task-service/`)
   - **Purpose**: Task creation, lifecycle management, and routing
   - **Port**: 8001
   - **Database**: PostgreSQL (tasks, priorities, routing rules)
   - **API**: REST endpoints for task CRUD operations

2. **User Service** (`user-service/`)
   - **Purpose**: User management, authentication, and profiles
   - **Port**: 8002
   - **Database**: PostgreSQL (users, roles, permissions)
   - **API**: REST endpoints for user management

3. **Tenant Service** (`tenant-service/`)
   - **Purpose**: Multi-tenant organization management
   - **Port**: 8003
   - **Database**: PostgreSQL (tenants, organization units, hierarchy)
   - **API**: REST endpoints for tenant operations

4. **Assignment Service** (`assignment-service/`)
   - **Purpose**: Task assignment, approval workflows, and routing
   - **Port**: 8004
   - **Database**: PostgreSQL (assignments, approvals, workflow states)
   - **API**: REST endpoints for assignment operations

5. **Comment Service** (`comment-service/`)
   - **Purpose**: Comments, notes, and communication on tasks
   - **Port**: 8005
   - **Database**: PostgreSQL (comments, attachments, notifications)
   - **API**: REST endpoints for commenting system

6. **Authority Service** (`authority-service/`)
   - **Purpose**: Authority recommendations and compliance checking
   - **Port**: 8006
   - **Database**: PostgreSQL (authorities, positions, compliance rules)
   - **API**: REST endpoints for authority management

### Infrastructure Services

7. **API Gateway** (`api-gateway/`)
   - **Purpose**: Request routing, authentication, rate limiting
   - **Port**: 8000
   - **Technology**: FastAPI with service discovery
   - **Features**: JWT auth, request routing, load balancing

8. **Common** (`common/`)
   - **Purpose**: Shared libraries, models, and utilities
   - **Contents**: Database schemas, authentication, logging, monitoring

## Microservice Design Principles

### 1. **Single Responsibility**
- Each service owns one business domain
- Clear service boundaries
- Independent data models

### 2. **Database Per Service**
- Each service has its own database schema
- No direct database access between services
- Event-driven data synchronization when needed

### 3. **Independent Deployment**
- Each service has its own Dockerfile
- Independent CI/CD pipelines
- Can be deployed and scaled separately

### 4. **Communication Patterns**
- **Synchronous**: REST APIs for direct queries
- **Asynchronous**: Message queues for events (future)
- **Service Discovery**: API Gateway routes requests

### 5. **Fault Tolerance**
- Circuit breaker pattern for external calls
- Graceful degradation
- Health checks and monitoring

## Development Workflow

### Task Creation and Assignment Flow:
```
1. POST /api/v2/tasks → Task Service
2. Task Service → User Service (validate creator)
3. Task Service → Tenant Service (validate organization)
4. Task Service creates task
5. POST /api/v2/assignments → Assignment Service
6. Assignment Service → Authority Service (authority checks)
7. Assignment Service creates assignment
8. POST /api/v2/comments → Comment Service (optional)
```

### Service Communication:
```
API Gateway (8000)
├── Task Service (8001)
├── User Service (8002)
├── Tenant Service (8003)
├── Assignment Service (8004)
├── Comment Service (8005)
└── Authority Service (8006)
```

## Environment Configuration

Each service uses environment variables for configuration:
- `DATABASE_URL`: Service-specific database connection
- `SERVICE_PORT`: Port for the service (8001-8006)
- `API_GATEWAY_URL`: URL of the API gateway
- `JWT_SECRET_KEY`: Shared secret for authentication
- `LOG_LEVEL`: Logging configuration

## Deployment

### Docker Compose (Development)
```bash
docker-compose up --build
```

### Kubernetes (Production)
Each service has its own deployment, service, and configmap definitions.

### Scaling
```bash
# Scale individual services
kubectl scale deployment task-service --replicas=3
kubectl scale deployment assignment-service --replicas=2
```

## Monitoring and Observability

- **Health Checks**: Each service exposes `/health` endpoint
- **Metrics**: Prometheus metrics on `/metrics` endpoint
- **Logging**: Structured JSON logging
- **Tracing**: Distributed tracing with correlation IDs

## Security

- **Authentication**: JWT tokens validated by API Gateway
- **Authorization**: Role-based access control per service
- **Network**: Services communicate within private network
- **Secrets**: Environment variables and secret management