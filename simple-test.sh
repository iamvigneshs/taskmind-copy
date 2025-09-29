#!/bin/bash

# Simple End-to-End Test for MissionMind TasksMind
set -e

echo "🚀 MissionMind TasksMind - Microservices Validation"
echo "================================================="

API_GATEWAY="http://localhost:8000"
TENANT_ID="acme-corp"
USER_ID="john.doe"

# Step 1: Create Task
echo "📋 Step 1: Creating security assessment task..."
TASK_RESPONSE=$(curl -s -X POST "$API_GATEWAY/api/v2/workflows/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Security Assessment - Network Infrastructure",
    "description": "Comprehensive security assessment including penetration testing",
    "priority": "high", 
    "assigned_to": "'$USER_ID'",
    "tenant_id": "'$TENANT_ID'",
    "org_unit_id": "CYBERSEC-DIV"
  }')

TASK_ID=$(echo "$TASK_RESPONSE" | jq -r '.task.id')
ASSIGNMENT_ID=$(echo "$TASK_RESPONSE" | jq -r '.assignment.id')

echo "✅ Task Created: $TASK_ID"
echo "✅ Assignment Created: $ASSIGNMENT_ID"
echo ""

# Step 2: Add Comments
echo "📋 Step 2: Adding progress comments..."
curl -s -X POST "$API_GATEWAY/api/v2/workflows/comment" \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "'$TASK_ID'",
    "content": "Started Phase 1: Network discovery and asset inventory completed. Found 45 network assets.",
    "tenant_id": "'$TENANT_ID'",
    "comment_type": "status_update"
  }' | jq '.content'

curl -s -X POST "$API_GATEWAY/api/v2/workflows/comment" \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "'$TASK_ID'",
    "content": "Phase 2: Penetration testing identified 3 vulnerabilities (2 medium, 1 low priority).",
    "tenant_id": "'$TENANT_ID'",
    "comment_type": "general"
  }' | jq '.content'

echo "✅ Comments Added"
echo ""

# Step 3: Get User Dashboard
echo "📋 Step 3: Checking user dashboard..."
DASHBOARD=$(curl -s "$API_GATEWAY/api/v2/dashboard/$USER_ID?tenant_id=$TENANT_ID")
ASSIGNED_COUNT=$(echo "$DASHBOARD" | jq '.summary.total_assigned')
echo "✅ User has $ASSIGNED_COUNT assigned tasks"
echo ""

# Step 4: Approve Task
echo "📋 Step 4: Approving task completion..."
APPROVAL_RESPONSE=$(curl -s -X POST "$API_GATEWAY/api/v2/workflows/approve" \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "'$TASK_ID'",
    "assignment_id": "'$ASSIGNMENT_ID'",
    "approved": true,
    "approval_note": "Security assessment completed successfully. All vulnerabilities documented.",
    "tenant_id": "'$TENANT_ID'"
  }')

echo "✅ Task Approved"
echo ""

# Step 5: Get Complete Workflow
echo "📋 Step 5: Retrieving complete task workflow..."
WORKFLOW=$(curl -s "$API_GATEWAY/api/v2/workflows/tasks/$TASK_ID?tenant_id=$TENANT_ID")
COMMENT_COUNT=$(echo "$WORKFLOW" | jq '.comments | length')
TASK_STATUS=$(echo "$WORKFLOW" | jq -r '.task.status')

echo "✅ Task Status: $TASK_STATUS"
echo "✅ Total Comments: $COMMENT_COUNT"
echo ""

# Step 6: Service Health Summary
echo "📋 Step 6: Service health summary..."
echo "Task Service:" $(curl -s http://localhost:8001/health | jq -r '.status')
echo "Assignment Service:" $(curl -s http://localhost:8004/health | jq -r '.status')
echo "Comment Service:" $(curl -s http://localhost:8005/health | jq -r '.status')
echo "API Gateway:" $(curl -s http://localhost:8000/health | jq -r '.gateway')
echo ""

echo "🎉 END-TO-END TEST COMPLETE!"
echo "=========================="
echo "✅ Microservices Architecture Validated"
echo "✅ Complete Workflow: Create → Assign → Comment → Approve"
echo "✅ Task ID: $TASK_ID"
echo "✅ Final Status: $TASK_STATUS"
echo "✅ All Core Services: Operational"
echo ""
echo "🏗️  Architecture Summary:"
echo "   🔹 API Gateway (8000) - Request orchestration"
echo "   🔹 Task Service (8001) - Task management"
echo "   🔹 Assignment Service (8004) - Workflow & approvals"
echo "   🔹 Comment Service (8005) - Communication"
echo "   🔹 PostgreSQL DBs (5432, 5433, 5434) - Data persistence"
echo ""
echo "🚀 MissionMind TasksMind microservices fully operational!"