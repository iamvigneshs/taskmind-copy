# Local Development Setup Guide

**Environment**: Development workstation  
**Architecture**: Microservices with Docker Compose  
**Target OS**: macOS, Linux, Windows (WSL2)

## 🎯 Quick Start

### **1-Minute Setup**
```bash
# Clone repository
git clone <repository-url>
cd tasksmind

# Start all services
docker-compose -f docker-compose-simple.yml up -d --build

# Verify system
./simple-test.sh

# Access API Gateway
open http://localhost:8000/docs
```

## 📋 Prerequisites

### **Required Software**

#### **Docker & Docker Compose**
```bash
# Install Docker Desktop (macOS/Windows)
# Download from: https://www.docker.com/products/docker-desktop

# Install Docker (Linux)
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### **Development Tools**
```bash
# Install jq for JSON processing
brew install jq  # macOS
sudo apt-get install jq  # Ubuntu
choco install jq  # Windows

# Install curl for API testing
# (Usually pre-installed on most systems)

# Optional: Install httpie for better API testing
pip install httpie
```

#### **Python Development (Optional)**
```bash
# Python 3.11+ for local service development
python3 --version  # Should be 3.11+

# Virtual environment
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r services/task-service/requirements.txt
```

### **System Requirements**

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| RAM | 8GB | 16GB+ |
| CPU | 2 cores | 4+ cores |
| Storage | 10GB free | 20GB+ free |
| Network | Broadband | Broadband |

## 🏗️ Development Environment

### **Directory Structure**
```
tasksmind/
├── services/                    # Microservices code
│   ├── api-gateway/            # API Gateway (Port 8000)
│   ├── task-service/           # Task Service (Port 8001)
│   ├── assignment-service/     # Assignment Service (Port 8004)
│   ├── comment-service/        # Comment Service (Port 8005)
│   ├── user-service/           # User Service (Port 8002) - Future
│   └── tenant-service/         # Tenant Service (Port 8003) - Future
├── k8s/                        # Kubernetes deployment files
├── docs/                       # Documentation
├── docker-compose-simple.yml   # Development Docker Compose
├── simple-test.sh              # End-to-end test script
└── README.md                   # Project overview
```

### **Service Ports**
| Service | Port | Purpose |
|---------|------|---------|
| API Gateway | 8000 | Main entry point |
| Task Service | 8001 | Task management |
| User Service | 8002 | User management (future) |
| Tenant Service | 8003 | Multi-tenancy (future) |
| Assignment Service | 8004 | Assignment workflow |
| Comment Service | 8005 | Communication |
| Authority Service | 8006 | Authority management (future) |

### **Database Ports**
| Database | Port | Service |
|----------|------|---------|
| Tasks PostgreSQL | 5432 | Task Service |
| Assignments PostgreSQL | 5433 | Assignment Service |
| Comments PostgreSQL | 5434 | Comment Service |

## 🚀 Development Workflow

### **Option 1: Full Docker Compose (Recommended)**

#### **Start All Services**
```bash
# Start all services with build
docker-compose -f docker-compose-simple.yml up -d --build

# View logs
docker-compose -f docker-compose-simple.yml logs -f

# Check service status
docker-compose -f docker-compose-simple.yml ps
```

#### **Service Management**
```bash
# Restart specific service
docker-compose -f docker-compose-simple.yml restart task-service

# Rebuild and restart service
docker-compose -f docker-compose-simple.yml up -d --build task-service

# Scale service
docker-compose -f docker-compose-simple.yml up -d --scale task-service=2

# Stop all services
docker-compose -f docker-compose-simple.yml down
```

#### **Database Access**
```bash
# Connect to Tasks database
docker exec -it tasksmind_postgres-tasks_1 psql -U taskuser -d tasksmind_tasks

# Connect to Assignments database
docker exec -it tasksmind_postgres-assignments_1 psql -U assignuser -d tasksmind_assignments

# Connect to Comments database
docker exec -it tasksmind_postgres-comments_1 psql -U commentuser -d tasksmind_comments
```

### **Option 2: Hybrid Development**

#### **Run Databases in Docker + Services Locally**

1. **Start Only Databases**:
```bash
# Start only PostgreSQL databases
docker-compose -f docker-compose-simple.yml up -d postgres-tasks postgres-assignments postgres-comments
```

2. **Set Environment Variables**:
```bash
export DATABASE_URL="postgresql://taskuser:taskpass123@localhost:5432/tasksmind_tasks"
export TASK_SERVICE_URL="http://localhost:8001"
export ASSIGNMENT_SERVICE_URL="http://localhost:8004"
export COMMENT_SERVICE_URL="http://localhost:8005"
```

3. **Run Services Locally**:
```bash
# Terminal 1: Task Service
cd services/task-service
pip install -r requirements.txt
python main.py

# Terminal 2: Assignment Service
cd services/assignment-service
pip install -r requirements.txt
export DATABASE_URL="postgresql://assignuser:assignpass123@localhost:5433/tasksmind_assignments"
python main.py

# Terminal 3: Comment Service  
cd services/comment-service
pip install -r requirements.txt
export DATABASE_URL="postgresql://commentuser:commentpass123@localhost:5434/tasksmind_comments"
python main.py

# Terminal 4: API Gateway
cd services/api-gateway
pip install -r requirements.txt
python main.py
```

### **Option 3: Individual Service Development**

#### **Single Service Development**
```bash
# Start only required dependencies
docker-compose -f docker-compose-simple.yml up -d postgres-tasks

# Work on Task Service
cd services/task-service

# Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://taskuser:taskpass123@localhost:5432/tasksmind_tasks"
export SERVICE_PORT=8001

# Run with hot reload
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

## 🧪 Testing & Validation

### **Health Checks**
```bash
# Check all services
./simple-test.sh

# Individual service health
curl http://localhost:8000/health  # API Gateway
curl http://localhost:8001/health  # Task Service
curl http://localhost:8004/health  # Assignment Service
curl http://localhost:8005/health  # Comment Service
```

### **API Testing**

#### **Using curl**
```bash
# Create a task
curl -X POST http://localhost:8000/api/v2/workflows/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Development Test Task",
    "description": "Testing local development environment",
    "priority": "medium",
    "assigned_to": "dev.user",
    "tenant_id": "dev-tenant"
  }' | jq .

# List tasks
curl -s "http://localhost:8000/api/v2/tasks/tasks?tenant_id=dev-tenant" | jq .

# Get user dashboard
curl -s "http://localhost:8000/api/v2/dashboard/dev.user?tenant_id=dev-tenant" | jq .
```

#### **Using HTTPie**
```bash
# Install httpie
pip install httpie

# Create task with HTTPie
http POST localhost:8000/api/v2/workflows/tasks \
  title="HTTPie Test Task" \
  tenant_id="dev-tenant" \
  priority="high"

# Get API info
http GET localhost:8000/api/v2/info
```

### **Interactive API Documentation**
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Task Service**: http://localhost:8001/docs
- **Assignment Service**: http://localhost:8004/docs
- **Comment Service**: http://localhost:8005/docs

## 🔧 Development Tools & Tips

### **Code Development**

#### **VS Code Setup**
```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "python.sortImports.args": ["--profile", "black"],
  "files.associations": {
    "*.yml": "yaml",
    "*.yaml": "yaml"
  }
}
```

#### **Pre-commit Hooks**
```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### **Database Tools**

#### **pgAdmin (Optional)**
```bash
# Run pgAdmin in Docker
docker run -d \
  --name pgadmin \
  -p 5050:80 \
  -e PGADMIN_DEFAULT_EMAIL=admin@tasksmind.com \
  -e PGADMIN_DEFAULT_PASSWORD=admin123 \
  dpage/pgadmin4

# Access at http://localhost:5050
```

#### **Database Migration Scripts**
```bash
# services/task-service/migrate.py
python3 -c "
from main import engine
from sqlmodel import SQLModel
SQLModel.metadata.create_all(engine)
print('✅ Task Service tables created')
"
```

### **Logging & Debugging**

#### **View Service Logs**
```bash
# All services
docker-compose -f docker-compose-simple.yml logs -f

# Specific service
docker-compose -f docker-compose-simple.yml logs -f task-service

# Follow logs with timestamps
docker-compose -f docker-compose-simple.yml logs -f -t api-gateway
```

#### **Debug Mode**
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run service with debug
cd services/task-service
python -m pdb main.py
```

### **Performance Testing**

#### **Load Testing with curl**
```bash
# Simple load test
for i in {1..50}; do
  curl -X POST http://localhost:8000/api/v2/workflows/tasks \
    -H "Content-Type: application/json" \
    -d '{
      "title": "Load Test Task '$i'",
      "tenant_id": "load-test",
      "priority": "medium"
    }' &
done
wait
echo "Load test completed"
```

#### **Monitor Resource Usage**
```bash
# Docker container stats
docker stats

# Specific containers
docker stats tasksmind_task-service_1 tasksmind_api-gateway_1
```

## 🐛 Troubleshooting

### **Common Issues**

#### **Port Already in Use**
```bash
# Find process using port
lsof -i :8000
sudo netstat -tulpn | grep 8000

# Kill process
kill -9 <PID>
```

#### **Docker Issues**
```bash
# Clean up Docker
docker system prune -f
docker volume prune -f

# Restart Docker service (Linux)
sudo systemctl restart docker

# Reset Docker Desktop (macOS/Windows)
# Docker Desktop > Troubleshoot > Reset to factory defaults
```

#### **Database Connection Issues**
```bash
# Check database containers
docker-compose -f docker-compose-simple.yml ps

# Check database logs
docker-compose -f docker-compose-simple.yml logs postgres-tasks

# Test database connection
docker exec tasksmind_postgres-tasks_1 pg_isready -U taskuser
```

#### **Service Communication Issues**
```bash
# Check Docker network
docker network ls
docker network inspect tasksmind_default

# Test service connectivity
docker exec tasksmind_api-gateway_1 curl -f http://task-service:8001/health
```

### **Debug Checklist**

- [ ] All containers running: `docker-compose ps`
- [ ] Database connections healthy: `curl localhost:8001/health`
- [ ] Services can communicate: `docker logs tasksmind_api-gateway_1`
- [ ] Ports not conflicting: `lsof -i :8000-8006`
- [ ] Environment variables set correctly
- [ ] Database schemas created: Check service logs

### **Environment Reset**
```bash
# Complete environment reset
docker-compose -f docker-compose-simple.yml down -v
docker system prune -f
docker volume prune -f
docker-compose -f docker-compose-simple.yml up -d --build

# Verify reset
./simple-test.sh
```

## 🔄 Development Workflow

### **Feature Development Process**

1. **Create Feature Branch**:
```bash
git checkout -b feature/new-task-feature
```

2. **Start Development Environment**:
```bash
docker-compose -f docker-compose-simple.yml up -d --build
```

3. **Make Changes**:
   - Edit service code
   - Update API documentation
   - Add tests

4. **Test Changes**:
```bash
# Run end-to-end test
./simple-test.sh

# Test specific functionality
curl -X POST localhost:8000/api/v2/workflows/tasks -d '{"title":"Test",...}'
```

5. **Commit Changes**:
```bash
git add .
git commit -m "feat: add new task feature"
git push origin feature/new-task-feature
```

### **Code Quality Standards**

- **Python**: Follow PEP 8, use Black formatter
- **API Design**: RESTful principles, OpenAPI documentation
- **Testing**: Unit tests + integration tests
- **Documentation**: Update relevant docs
- **Docker**: Multi-stage builds, security best practices

### **Performance Considerations**

- **Database Queries**: Use indexes, avoid N+1 queries
- **API Responses**: Paginate large datasets
- **Caching**: Use appropriate caching strategies
- **Resource Usage**: Monitor memory and CPU usage

---

This comprehensive development setup guide enables efficient local development of the MissionMind TasksMind microservices platform with full testing and debugging capabilities.