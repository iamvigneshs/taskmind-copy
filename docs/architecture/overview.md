# Architecture Overview - MissionMind TasksMind

**Version**: 2.0.0  
**Architecture Pattern**: Microservices  
**Design Philosophy**: Domain-Driven Design with Service-Oriented Architecture

## 🎯 System Overview

MissionMind TasksMind is a microservices-based task orchestration platform designed for military, government, and commercial organizations. The system provides comprehensive task management capabilities with multi-tenant support, configurable workflows, and enterprise-grade security.

## 🏗️ High-Level Architecture

### **Architecture Diagram**
```
┌─────────────────────────────────────────────────────────────────┐
│                          CLIENT TIER                            │
├─────────────────────────────────────────────────────────────────┤
│  Web Apps    │  Mobile Apps  │  Desktop Apps  │  External APIs  │
└─────────────────────┬───────────────────────────────────────────┘
                      │ HTTPS/REST
┌─────────────────────▼───────────────────────────────────────────┐
│                       API GATEWAY                               │
│                     (Port 8000)                                 │
│  • Request Routing   • Authentication   • Rate Limiting         │
│  • Load Balancing   • Request/Response Transformation          │
└─────────────┬───────────────┬───────────────┬───────────────────┘
              │               │               │
         ┌────▼────┐    ┌────▼────┐    ┌────▼────┐
         │  TASK   │    │ASSIGNMENT│    │COMMENT  │
         │SERVICE  │    │ SERVICE  │    │SERVICE  │
         │ :8001   │    │  :8004   │    │ :8005   │
         └────┬────┘    └────┬────┘    └────┬────┘
              │              │              │
         ┌────▼────┐    ┌────▼────┐    ┌────▼────┐
         │ Tasks   │    │Assign.  │    │Comments │
         │Database │    │Database │    │Database │
         │ :5432   │    │ :5433   │    │ :5434   │
         └─────────┘    └─────────┘    └─────────┘
```

## 🔧 Service Architecture

### **1. API Gateway (Port 8000)**
**Responsibility**: Request orchestration and service coordination

**Key Functions**:
- **Service Discovery**: Routes requests to appropriate microservices
- **Request Aggregation**: Combines data from multiple services
- **Authentication**: JWT token validation (future implementation)
- **Rate Limiting**: Per-tenant and per-user request limits
- **Load Balancing**: Distributes load across service instances

**Technologies**: FastAPI, httpx, Pydantic

### **2. Task Service (Port 8001)**
**Responsibility**: Core task management and lifecycle

**Key Functions**:
- Task creation with unique ID generation
- Priority scoring and routing algorithms
- Task lifecycle management (pending → assigned → approved → completed)
- Due date tracking and alerting
- Multi-tenant task isolation

**Database Schema**:
```sql
CREATE TABLE task (
    id VARCHAR PRIMARY KEY,
    title VARCHAR NOT NULL,
    description TEXT,
    priority VARCHAR DEFAULT 'medium',
    status VARCHAR DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    due_date TIMESTAMP,
    created_by VARCHAR,
    assigned_to VARCHAR,
    approved_by VARCHAR,
    tenant_id VARCHAR NOT NULL,
    org_unit_id VARCHAR,
    priority_score FLOAT DEFAULT 0.5,
    routing_rules TEXT
);
```

### **3. Assignment Service (Port 8004)**
**Responsibility**: Task assignments and approval workflows

**Key Functions**:
- Assignment creation and tracking
- Approval workflow management
- Authority-based approval routing
- Assignment completion tracking
- Task routing between users

**Database Schemas**:
```sql
CREATE TABLE assignment (
    id VARCHAR PRIMARY KEY,
    task_id VARCHAR NOT NULL,
    assigned_to VARCHAR NOT NULL,
    assigned_by VARCHAR NOT NULL,
    tenant_id VARCHAR NOT NULL,
    status VARCHAR DEFAULT 'pending',
    assigned_at TIMESTAMP DEFAULT NOW(),
    due_date TIMESTAMP,
    completed_at TIMESTAMP,
    note TEXT,
    priority VARCHAR DEFAULT 'medium'
);

CREATE TABLE approval (
    id VARCHAR PRIMARY KEY,
    task_id VARCHAR NOT NULL,
    assignment_id VARCHAR NOT NULL,
    approver_id VARCHAR NOT NULL,
    tenant_id VARCHAR NOT NULL,
    status VARCHAR DEFAULT 'pending',
    approved_at TIMESTAMP,
    approval_note TEXT,
    authority_level VARCHAR,
    requires_additional_approval BOOLEAN DEFAULT FALSE
);
```

### **4. Comment Service (Port 8005)**
**Responsibility**: Communication and activity tracking

**Key Functions**:
- Comment creation and threading
- Status update notifications
- Activity logging and audit trail
- Multi-type comments (general, status_update, approval_note)
- Visibility controls (internal/external)

**Database Schema**:
```sql
CREATE TABLE comment (
    id VARCHAR PRIMARY KEY,
    task_id VARCHAR NOT NULL,
    assignment_id VARCHAR,
    author_id VARCHAR NOT NULL,
    tenant_id VARCHAR NOT NULL,
    content TEXT NOT NULL,
    comment_type VARCHAR DEFAULT 'general',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_internal BOOLEAN DEFAULT FALSE,
    visibility VARCHAR DEFAULT 'all',
    priority VARCHAR DEFAULT 'normal'
);
```

## 🔄 Service Communication Patterns

### **1. Synchronous Communication**
- **HTTP REST APIs** for direct service-to-service calls
- **API Gateway Orchestration** for complex workflows
- **Circuit Breaker Pattern** for fault tolerance

### **2. Data Flow Patterns**

#### **Task Creation Workflow**:
```
1. Client → API Gateway: POST /api/v2/workflows/tasks
2. API Gateway → Task Service: POST /tasks
3. Task Service → Database: INSERT task
4. API Gateway → Assignment Service: POST /assignments (if assigned_to provided)
5. Assignment Service → Task Service: PUT /tasks/{id} (update assigned_to)
6. API Gateway → Comment Service: POST /comments (create initial comment)
7. API Gateway → Client: Complete workflow response
```

#### **Task Approval Workflow**:
```
1. Client → API Gateway: POST /api/v2/workflows/approve
2. API Gateway → Assignment Service: POST /approvals
3. Assignment Service → Assignment Service: PUT /approvals/{id}
4. Assignment Service → Task Service: PUT /tasks/{id} (update status)
5. API Gateway → Comment Service: POST /comments (approval comment)
6. API Gateway → Client: Approval response
```

## 💾 Data Architecture

### **Database Per Service Pattern**
Each microservice owns its data completely:

- **Task Service**: `tasksmind_tasks` database
- **Assignment Service**: `tasksmind_assignments` database  
- **Comment Service**: `tasksmind_comments` database

### **Multi-Tenancy Strategy**
- **Row-Level Security**: `tenant_id` in all tables
- **Data Isolation**: All queries filtered by tenant
- **Shared Database, Isolated Schemas**: Cost-effective isolation

### **Data Consistency**
- **Eventual Consistency**: Services synchronize via API calls
- **Compensating Actions**: Rollback mechanisms for failed workflows
- **Event Sourcing**: Future enhancement for audit trails

## 🔒 Security Architecture

### **Authentication & Authorization**
- **API Gateway**: Single entry point for authentication
- **JWT Tokens**: Stateless authentication (future implementation)
- **Role-Based Access Control**: Per-tenant permissions
- **Service-to-Service**: Internal network communication

### **Data Security**
- **Tenant Isolation**: Complete data separation
- **Encryption at Rest**: Database-level encryption
- **Encryption in Transit**: HTTPS/TLS for all communications
- **Secret Management**: Environment variables and secret stores

### **Network Security**
- **Private Networks**: Services communicate within VPC
- **API Gateway**: Single external endpoint
- **Database Security**: Private subnets with security groups
- **Container Security**: Non-root users, minimal base images

## 📊 Scalability Architecture

### **Horizontal Scaling**
- **Stateless Services**: All services can scale horizontally
- **Load Balancing**: API Gateway distributes requests
- **Database Sharding**: Future enhancement for large datasets
- **Cache Layer**: Future Redis implementation for performance

### **Auto-Scaling Triggers**
- **CPU Utilization**: > 70% triggers scale-up
- **Memory Usage**: > 80% triggers scale-up
- **Request Volume**: Queue depth-based scaling
- **Custom Metrics**: Task creation rate, approval backlog

### **Performance Targets**
- **API Response Time**: < 200ms for 95th percentile
- **Task Creation**: < 500ms end-to-end
- **Dashboard Loading**: < 100ms
- **Throughput**: 1000+ concurrent users per service instance

## 🔄 Deployment Architecture

### **Development Environment**
- **Docker Compose**: Local development stack
- **Hot Reloading**: Development-time code updates
- **Shared Networks**: Service-to-service communication
- **Volume Mounts**: Database persistence

### **Staging Environment**
- **Kubernetes**: Container orchestration
- **Service Mesh**: Future Istio implementation
- **Blue-Green Deployments**: Zero-downtime updates
- **Integration Testing**: Automated test suites

### **Production Environment**
- **Multi-AZ Deployment**: High availability
- **Auto-Scaling Groups**: Demand-based scaling
- **Load Balancers**: Application and network load balancing
- **Monitoring**: Comprehensive observability stack

## 🔍 Observability Architecture

### **Monitoring Stack**
- **Prometheus**: Metrics collection
- **Grafana**: Metrics visualization
- **ELK Stack**: Centralized logging (future)
- **Jaeger**: Distributed tracing (future)

### **Health Checks**
- **Service Health**: `/health` endpoints
- **Database Connectivity**: Connection pool monitoring
- **Dependency Health**: External service monitoring
- **Business Metrics**: Task completion rates, SLA tracking

### **Alerting**
- **Service Failures**: Immediate alerts
- **Performance Degradation**: Threshold-based alerts
- **Business KPIs**: Daily/weekly reports
- **Security Events**: Real-time security monitoring

## 🚀 Future Architecture Enhancements

### **Phase 2 Services**
- **User Service**: Authentication and user management
- **Tenant Service**: Organization and hierarchy management
- **Authority Service**: Military compliance and authority recommendations

### **Advanced Features**
- **Message Queue**: Asynchronous communication (RabbitMQ/Kafka)
- **Event Sourcing**: Complete audit trail and replay capability
- **CQRS**: Command Query Responsibility Segregation
- **API Versioning**: Multiple API version support

### **Platform Features**
- **Multi-Cloud**: AWS, Azure, GCP deployment options
- **Edge Computing**: Regional service deployment
- **Machine Learning**: Intelligent task routing and priority scoring
- **Mobile APIs**: GraphQL for mobile applications

---

This architecture provides a solid foundation for scalable, maintainable, and secure task management across military, government, and commercial organizations while maintaining the flexibility to evolve with changing requirements.