# AWS Production Deployment Guide

**Target Environment**: Amazon Web Services (AWS)  
**Architecture**: Microservices on Amazon EKS  
**High Availability**: Multi-AZ deployment with auto-scaling  
**Security**: VPC isolation with private subnets

## 🏗️ AWS Architecture Overview

### **Production Architecture Diagram**
```
                                ┌─────────────────────┐
                                │    Route 53 DNS     │
                                └──────────┬──────────┘
                                           │
                        ┌──────────────────▼──────────────────┐
                        │      Application Load Balancer      │
                        │             (ALB)                   │
                        └──────────┬─────────────┬────────────┘
                                   │             │
            ┌──────────────────────▼─────────────▼────────────────────┐
            │                   Amazon EKS                            │
            │                                                         │
            │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
            │  │ API Gateway │  │Task Service │  │Assign. Svc  │     │
            │  │   :8000     │  │   :8001     │  │   :8004     │     │
            │  └─────────────┘  └─────────────┘  └─────────────┘     │
            │                                                         │
            │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
            │  │Comment Svc  │  │User Service │  │Tenant Svc   │     │
            │  │   :8005     │  │   :8002     │  │   :8003     │     │
            │  └─────────────┘  └─────────────┘  └─────────────┘     │
            └─────────────────────────────────────────────────────────┘
                                           │
            ┌──────────────────────────────▼──────────────────────────────┐
            │                       Amazon RDS                            │
            │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
            │  │   Tasks     │  │ Assignments │  │  Comments   │         │
            │  │ PostgreSQL  │  │ PostgreSQL  │  │ PostgreSQL  │         │
            │  └─────────────┘  └─────────────┘  └─────────────┘         │
            └─────────────────────────────────────────────────────────────┘
```

## 🚀 Deployment Components

### **1. Amazon EKS (Kubernetes Service)**
**Purpose**: Container orchestration and service management

#### **Cluster Configuration**:
```yaml
# eks-cluster.yaml
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: tasksmind-production
  region: us-west-2
  version: "1.28"

availabilityZones:
  - us-west-2a
  - us-west-2b
  - us-west-2c

managedNodeGroups:
  - name: tasksmind-workers
    instanceType: m5.large
    minSize: 3
    maxSize: 10
    desiredCapacity: 6
    availabilityZones:
      - us-west-2a
      - us-west-2b
      - us-west-2c
    
    iam:
      withAddonPolicies:
        autoScaler: true
        cloudWatch: true
        ebs: true
        efs: true
        albIngress: true
    
    tags:
      Environment: production
      Application: tasksmind
      Team: platform

vpc:
  cidr: "10.0.0.0/16"
  nat:
    gateway: HighlyAvailable
  
  clusterEndpoints:
    privateAccess: true
    publicAccess: true
    publicAccessCIDRs:
      - "0.0.0.0/0"

cloudWatch:
  clusterLogging:
    enableTypes:
      - audit
      - authenticator
      - controllerManager
```

### **2. Amazon RDS (Managed PostgreSQL)**
**Purpose**: Managed database service with high availability

#### **Database Configuration**:
```yaml
# rds-config.yaml
Resources:
  TasksDatabase:
    Type: AWS::RDS::DBInstance
    Properties:
      DBInstanceIdentifier: tasksmind-tasks-prod
      DBInstanceClass: db.r5.xlarge
      Engine: postgres
      EngineVersion: "15.4"
      MasterUsername: taskuser
      MasterUserPassword: !Ref TasksDBPassword
      AllocatedStorage: 500
      StorageType: gp3
      StorageEncrypted: true
      MultiAZ: true
      BackupRetentionPeriod: 30
      DeletionProtection: true
      
      VpcSecurityGroups:
        - !Ref DatabaseSecurityGroup
      DBSubnetGroupName: !Ref DatabaseSubnetGroup
      
      Tags:
        - Key: Environment
          Value: production
        - Key: Service
          Value: task-service

  AssignmentsDatabase:
    Type: AWS::RDS::DBInstance
    Properties:
      DBInstanceIdentifier: tasksmind-assignments-prod
      DBInstanceClass: db.r5.large
      Engine: postgres
      EngineVersion: "15.4"
      MasterUsername: assignuser
      MasterUserPassword: !Ref AssignmentsDBPassword
      AllocatedStorage: 200
      StorageType: gp3
      StorageEncrypted: true
      MultiAZ: true
      BackupRetentionPeriod: 30
      
      VpcSecurityGroups:
        - !Ref DatabaseSecurityGroup
      DBSubnetGroupName: !Ref DatabaseSubnetGroup

  CommentsDatabase:
    Type: AWS::RDS::DBInstance
    Properties:
      DBInstanceIdentifier: tasksmind-comments-prod
      DBInstanceClass: db.r5.large
      Engine: postgres
      EngineVersion: "15.4"
      MasterUsername: commentuser
      MasterUserPassword: !Ref CommentsDBPassword
      AllocatedStorage: 300
      StorageType: gp3
      StorageEncrypted: true
      MultiAZ: true
      BackupRetentionPeriod: 30
      
      VpcSecurityGroups:
        - !Ref DatabaseSecurityGroup
      DBSubnetGroupName: !Ref DatabaseSubnetGroup
```

### **3. Application Load Balancer (ALB)**
**Purpose**: HTTP/HTTPS traffic distribution and SSL termination

#### **ALB Configuration**:
```yaml
# alb-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: tasksmind-ingress
  namespace: tasksmind
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/ssl-redirect: '443'
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:us-west-2:ACCOUNT:certificate/CERT-ID
    alb.ingress.kubernetes.io/health-check-path: /health
    alb.ingress.kubernetes.io/health-check-interval-seconds: '30'
    alb.ingress.kubernetes.io/health-check-timeout-seconds: '5'
    alb.ingress.kubernetes.io/healthy-threshold-count: '2'
    alb.ingress.kubernetes.io/unhealthy-threshold-count: '3'

spec:
  tls:
    - hosts:
        - api.tasksmind.com
      secretName: tasksmind-tls
  
  rules:
    - host: api.tasksmind.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: api-gateway
                port:
                  number: 8000
```

## 📋 Step-by-Step Deployment Guide

### **Prerequisites**

1. **AWS CLI Configuration**:
```bash
aws configure
# Enter AWS Access Key ID, Secret Key, Region (us-west-2)
```

2. **Required Tools**:
```bash
# Install eksctl
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin

# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

3. **AWS Permissions**:
   - EKS Full Access
   - EC2 Full Access
   - RDS Full Access
   - VPC Full Access
   - IAM permissions for service roles
   - Route53 (for DNS)
   - Certificate Manager (for SSL)

### **Phase 1: Infrastructure Setup**

#### **Step 1: Create EKS Cluster**
```bash
# Create EKS cluster
eksctl create cluster -f eks-cluster.yaml

# Verify cluster
kubectl get nodes
kubectl get namespaces
```

#### **Step 2: Create Namespace and RBAC**
```bash
# Create namespace
kubectl create namespace tasksmind

# Create service account for AWS Load Balancer Controller
eksctl create iamserviceaccount \
  --cluster=tasksmind-production \
  --namespace=kube-system \
  --name=aws-load-balancer-controller \
  --role-name AmazonEKSLoadBalancerControllerRole \
  --attach-policy-arn=arn:aws:iam::aws:policy/ElasticLoadBalancingFullAccess \
  --approve
```

#### **Step 3: Install AWS Load Balancer Controller**
```bash
# Add EKS Helm repository
helm repo add eks https://aws.github.io/eks-charts
helm repo update

# Install AWS Load Balancer Controller
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=tasksmind-production \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller
```

#### **Step 4: Create RDS Databases**
```bash
# Deploy RDS CloudFormation stack
aws cloudformation create-stack \
  --stack-name tasksmind-databases \
  --template-body file://rds-config.yaml \
  --parameters ParameterKey=TasksDBPassword,ParameterValue=SecurePassword123! \
               ParameterKey=AssignmentsDBPassword,ParameterValue=SecurePassword456! \
               ParameterKey=CommentsDBPassword,ParameterValue=SecurePassword789! \
  --capabilities CAPABILITY_IAM

# Wait for stack completion
aws cloudformation wait stack-create-complete --stack-name tasksmind-databases
```

### **Phase 2: Application Deployment**

#### **Step 5: Create Secrets**
```bash
# Database connection secrets
kubectl create secret generic database-secrets \
  --from-literal=task-db-url="postgresql://taskuser:SecurePassword123!@tasksmind-tasks-prod.cluster-xyz.us-west-2.rds.amazonaws.com:5432/tasksmind_tasks" \
  --from-literal=assignment-db-url="postgresql://assignuser:SecurePassword456!@tasksmind-assignments-prod.cluster-xyz.us-west-2.rds.amazonaws.com:5432/tasksmind_assignments" \
  --from-literal=comment-db-url="postgresql://commentuser:SecurePassword789!@tasksmind-comments-prod.cluster-xyz.us-west-2.rds.amazonaws.com:5432/tasksmind_comments" \
  -n tasksmind

# Application secrets
kubectl create secret generic app-secrets \
  --from-literal=jwt-secret-key="SuperSecretJWTKey123!" \
  --from-literal=encryption-key="AES256EncryptionKey!" \
  -n tasksmind
```

#### **Step 6: Deploy Container Images**

First, build and push images to Amazon ECR:

```bash
# Create ECR repositories
aws ecr create-repository --repository-name tasksmind/task-service --region us-west-2
aws ecr create-repository --repository-name tasksmind/assignment-service --region us-west-2
aws ecr create-repository --repository-name tasksmind/comment-service --region us-west-2
aws ecr create-repository --repository-name tasksmind/api-gateway --region us-west-2

# Get ECR login token
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin ACCOUNT.dkr.ecr.us-west-2.amazonaws.com

# Build and push images
docker build -t ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/tasksmind/task-service:latest ./services/task-service
docker push ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/tasksmind/task-service:latest

docker build -t ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/tasksmind/assignment-service:latest ./services/assignment-service
docker push ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/tasksmind/assignment-service:latest

docker build -t ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/tasksmind/comment-service:latest ./services/comment-service
docker push ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/tasksmind/comment-service:latest

docker build -t ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/tasksmind/api-gateway:latest ./services/api-gateway
docker push ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/tasksmind/api-gateway:latest
```

#### **Step 7: Deploy Microservices**
```bash
# Update image references in k8s manifests
sed -i 's|tasksmind/task-service:latest|ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/tasksmind/task-service:latest|g' k8s/deployments/task-service.yaml

# Deploy all services
kubectl apply -f k8s/deployments/ -n tasksmind
kubectl apply -f k8s/services/ -n tasksmind
kubectl apply -f k8s/configmaps/ -n tasksmind

# Deploy ingress
kubectl apply -f alb-ingress.yaml -n tasksmind
```

#### **Step 8: Verify Deployment**
```bash
# Check pod status
kubectl get pods -n tasksmind

# Check service status
kubectl get services -n tasksmind

# Check ingress
kubectl get ingress -n tasksmind

# Get ALB endpoint
kubectl get ingress tasksmind-ingress -n tasksmind -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

### **Phase 3: Monitoring and Observability**

#### **Step 9: Install Monitoring Stack**
```bash
# Add Prometheus Helm repository
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Install Prometheus
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
  --set prometheus.prometheusSpec.retention=30d \
  --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=100Gi

# Install Grafana (if not included in prometheus stack)
helm install grafana grafana/grafana \
  --namespace monitoring \
  --set adminPassword=SecureGrafanaPassword! \
  --set service.type=LoadBalancer
```

#### **Step 10: Configure CloudWatch Integration**
```bash
# Install AWS CloudWatch Agent
kubectl apply -f https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonset/container-insights-monitoring/cloudwatch-namespace.yaml

# Configure CloudWatch agent
kubectl create configmap cluster-info \
  --from-literal=cluster.name=tasksmind-production \
  --from-literal=logs.region=us-west-2 -n amazon-cloudwatch

kubectl apply -f https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonset/container-insights-monitoring/fluentd/fluentd.yaml
```

## 🔒 Security Configuration

### **1. Network Security**

#### **VPC Configuration**:
```yaml
# vpc-config.yaml
VPC:
  CIDR: "10.0.0.0/16"
  
PrivateSubnets:
  - CIDR: "10.0.1.0/24"  # us-west-2a
    AZ: us-west-2a
  - CIDR: "10.0.2.0/24"  # us-west-2b  
    AZ: us-west-2b
  - CIDR: "10.0.3.0/24"  # us-west-2c
    AZ: us-west-2c

PublicSubnets:
  - CIDR: "10.0.101.0/24"  # us-west-2a
    AZ: us-west-2a
  - CIDR: "10.0.102.0/24"  # us-west-2b
    AZ: us-west-2b
  - CIDR: "10.0.103.0/24"  # us-west-2c
    AZ: us-west-2c
```

#### **Security Groups**:
```yaml
# security-groups.yaml
DatabaseSecurityGroup:
  Rules:
    - Protocol: TCP
      Port: 5432
      Source: EKSWorkerNodeSecurityGroup
      Description: "PostgreSQL from EKS workers"

EKSWorkerNodeSecurityGroup:
  Rules:
    - Protocol: TCP
      Port: 8000-8006
      Source: ALBSecurityGroup
      Description: "API traffic from ALB"
    - Protocol: TCP
      Port: 443
      Source: "0.0.0.0/0"
      Description: "HTTPS from internet"

ALBSecurityGroup:
  Rules:
    - Protocol: TCP
      Port: 443
      Source: "0.0.0.0/0"
      Description: "HTTPS from internet"
    - Protocol: TCP
      Port: 80
      Source: "0.0.0.0/0"
      Description: "HTTP redirect to HTTPS"
```

### **2. IAM Roles and Policies**

#### **EKS Service Role**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "eks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

#### **Worker Node Instance Profile**:
```bash
# Create IAM role for worker nodes
aws iam create-role \
  --role-name TasksMindWorkerNodeInstanceRole \
  --assume-role-policy-document file://worker-node-trust-policy.json

# Attach required policies
aws iam attach-role-policy \
  --role-name TasksMindWorkerNodeInstanceRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy

aws iam attach-role-policy \
  --role-name TasksMindWorkerNodeInstanceRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy

aws iam attach-role-policy \
  --role-name TasksMindWorkerNodeInstanceRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly
```

### **3. SSL/TLS Configuration**

#### **ACM Certificate**:
```bash
# Request SSL certificate
aws acm request-certificate \
  --domain-name api.tasksmind.com \
  --subject-alternative-names "*.tasksmind.com" \
  --validation-method DNS \
  --region us-west-2

# Note the certificate ARN for ALB configuration
```

#### **Route 53 DNS Configuration**:
```bash
# Create hosted zone
aws route53 create-hosted-zone \
  --name tasksmind.com \
  --caller-reference "$(date +%s)"

# Create DNS record for ALB
aws route53 change-resource-record-sets \
  --hosted-zone-id ZONE_ID \
  --change-batch file://dns-record.json
```

## 📊 Auto-Scaling Configuration

### **Horizontal Pod Autoscaler (HPA)**
```yaml
# hpa-config.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-gateway-hpa
  namespace: tasksmind
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-gateway
  minReplicas: 2
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
```

### **Cluster Autoscaler**
```yaml
# cluster-autoscaler.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cluster-autoscaler
  namespace: kube-system
spec:
  template:
    spec:
      containers:
      - image: k8s.gcr.io/autoscaling/cluster-autoscaler:v1.28.0
        name: cluster-autoscaler
        resources:
          limits:
            cpu: 100m
            memory: 300Mi
          requests:
            cpu: 100m
            memory: 300Mi
        command:
        - ./cluster-autoscaler
        - --v=4
        - --stderrthreshold=info
        - --cloud-provider=aws
        - --skip-nodes-with-local-storage=false
        - --expander=least-waste
        - --node-group-auto-discovery=asg:tag=k8s.io/cluster-autoscaler/enabled,k8s.io/cluster-autoscaler/tasksmind-production
        - --balance-similar-node-groups
        - --skip-nodes-with-system-pods=false
```

## 🔧 Operational Procedures

### **Deployment Pipeline**

#### **CI/CD with GitHub Actions**:
```yaml
# .github/workflows/deploy-aws.yml
name: Deploy to AWS Production
on:
  push:
    branches: [main]

env:
  AWS_REGION: us-west-2
  EKS_CLUSTER_NAME: tasksmind-production

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}
      
      - name: Login to Amazon ECR
        uses: aws-actions/amazon-ecr-login@v1
      
      - name: Build and push images
        run: |
          docker build -t $ECR_REGISTRY/tasksmind/api-gateway:$GITHUB_SHA ./services/api-gateway
          docker push $ECR_REGISTRY/tasksmind/api-gateway:$GITHUB_SHA
      
      - name: Update kubeconfig
        run: |
          aws eks update-kubeconfig --name $EKS_CLUSTER_NAME --region $AWS_REGION
      
      - name: Deploy to EKS
        run: |
          sed -i 's|ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/tasksmind/api-gateway:latest|'$ECR_REGISTRY'/tasksmind/api-gateway:'$GITHUB_SHA'|g' k8s/deployments/api-gateway.yaml
          kubectl apply -f k8s/deployments/ -n tasksmind
          kubectl rollout status deployment/api-gateway -n tasksmind
```

### **Backup and Recovery**

#### **Database Backup**:
```bash
# Automated RDS snapshots are enabled
# Manual snapshot for immediate backup
aws rds create-db-snapshot \
  --db-instance-identifier tasksmind-tasks-prod \
  --db-snapshot-identifier tasksmind-tasks-manual-$(date +%Y%m%d-%H%M)

# Cross-region backup
aws rds copy-db-snapshot \
  --source-db-snapshot-identifier tasksmind-tasks-manual-$(date +%Y%m%d-%H%M) \
  --target-db-snapshot-identifier tasksmind-tasks-backup-$(date +%Y%m%d-%H%M) \
  --source-region us-west-2 \
  --target-region us-east-1
```

#### **Application State Backup**:
```bash
# Backup Kubernetes resources
kubectl get all -n tasksmind -o yaml > tasksmind-k8s-backup-$(date +%Y%m%d).yaml

# Backup secrets
kubectl get secrets -n tasksmind -o yaml > tasksmind-secrets-backup-$(date +%Y%m%d).yaml
```

### **Disaster Recovery**

#### **Recovery Time Objectives (RTO)**:
- **Database Recovery**: 15 minutes (RDS Multi-AZ)
- **Application Recovery**: 10 minutes (EKS auto-healing)
- **Full System Recovery**: 30 minutes

#### **Recovery Point Objectives (RPO)**:
- **Database Data Loss**: < 5 minutes (automated backups)
- **Application State**: 0 (stateless services)

#### **DR Procedures**:
```bash
# 1. Failover RDS to standby (automatic in Multi-AZ)
aws rds failover-db-cluster --db-cluster-identifier tasksmind-cluster

# 2. Scale up EKS nodes if needed
eksctl scale nodegroup --cluster=tasksmind-production --nodes=10 --name=tasksmind-workers

# 3. Verify service health
kubectl get pods -n tasksmind
curl -f https://api.tasksmind.com/health
```

## 💰 Cost Optimization

### **Resource Right-Sizing**

#### **EKS Node Groups**:
- **Production**: m5.large (2 vCPU, 8GB RAM) - $0.096/hour
- **Scaling**: Up to m5.xlarge during peak load
- **Reserved Instances**: 1-year term for 40% cost savings

#### **RDS Instances**:
- **Tasks DB**: db.r5.xlarge for high read/write operations
- **Assignments/Comments**: db.r5.large for moderate load
- **Reserved Instances**: 1-year term for 35% cost savings

#### **Data Transfer Costs**:
- Use CloudFront CDN for static assets
- Enable VPC endpoints for S3/ECR access
- Optimize inter-AZ data transfer

### **Cost Monitoring**:
```bash
# Set up billing alerts
aws budgets create-budget \
  --account-id ACCOUNT_ID \
  --budget file://tasksmind-budget.json \
  --notifications-with-subscribers file://budget-notifications.json
```

## 🎯 Performance Optimization

### **Database Performance**:
```sql
-- Optimize PostgreSQL for production
ALTER SYSTEM SET shared_buffers = '2GB';
ALTER SYSTEM SET effective_cache_size = '6GB';
ALTER SYSTEM SET maintenance_work_mem = '512MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.7;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;

-- Create performance indexes
CREATE INDEX CONCURRENTLY idx_task_tenant_status ON task(tenant_id, status);
CREATE INDEX CONCURRENTLY idx_assignment_tenant_user ON assignment(tenant_id, assigned_to);
CREATE INDEX CONCURRENTLY idx_comment_task_created ON comment(task_id, created_at);
```

### **Application Performance**:
- **Connection Pooling**: Configure optimal pool sizes
- **Caching**: Implement Redis for frequently accessed data
- **CDN**: CloudFront for API responses and static assets

---

This comprehensive AWS deployment guide provides production-ready infrastructure for MissionMind TasksMind microservices with enterprise-grade security, scalability, and reliability suitable for military, government, and commercial environments.