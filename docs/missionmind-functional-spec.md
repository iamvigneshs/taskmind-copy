# MissionMind Agentic Approval Layer Specification

## 1. Functional Requirements

### 1.1 Mission Objective
Deliver an agentic approval and task-routing layer for MissionMind.ai that orchestrates ETMS2 workflows, shortens staffing cycles, and improves decision quality through AI-driven insights.

### 1.2 Stakeholders
- Action officers, reviewers, approvers, and staff leaders leveraging MissionMind.ai assistants.
- MissionMind.ai digital workers executing automations.
- Compliance and audit teams requiring traceability.
- System administrators overseeing integrations and security posture.

### 1.3 Core Capabilities
- **Smart Task Routing & Prioritization**: Classify and rank taskers using textual and metadata inputs; auto-route to optimal org units or personnel while balancing workload.
- **Draft Quality Checks**: Run pre-staffing compliance reviews against AR 25-50/25-30 formatting and publishing rules; flag issues before human review.
- **Authority Recommendation**: Suggest the lowest appropriate approval authority based on policy area, echelon, and historical precedents.
- **Comment Summarization**: Cluster duplicate or conflicting comments into themes and highlight nonconcurrence rationales for quick adjudication.
- **Predictive Staffing Insights**: Surface cycle times, bottleneck predictions, approver availability, and risk dashboards for leadership.
- **Workflow Automation**: Auto-generate drafts, fill templates, track suspense compliance, trigger reminders via Army 365, and update ETMS2 data stores.

### 1.4 Operational Constraints
- Integrate with ETMS2 APIs and Army 365 (Teams/Outlook) environments.
- Enforce data handling for classification levels (U/C/S) and ARIMS record retention.
- Maintain end-to-end audit logging and support external audits.
- Operate within Army cybersecurity policies, including network segmentation and identity assurance.
- Deliver high availability during mission-critical cycles with graceful degradation fallbacks.

### 1.5 Success Measures
- Reduced average routing and coordination time.
- Decreased suspense delinquency rate and improved on-time completion.
- Higher first-pass acceptance of draft documents.
- Faster authority assignment decisions with fewer escalations.
- Improved user satisfaction scores for ETMS2 task management experiences.

## 2. API Specification

**Base URL**: `https://mock-etms2.local/api`

**Authentication**: Azure Army 365 bearer token; all endpoints require TLS and audit logging.

### 2.1 Tasks
- `GET /tasks?status=<status>&due_before=<date>&org=<org>`: Filter tasks by state, suspense window, and originating organization.
- `POST /tasks`: Register a draft task (mission simulations or agent-generated tasks). Requires payload matching the Task schema.
- `GET /tasks/{id}`: Retrieve full task metadata, including attachments and related tasks.
- `PATCH /tasks/{id}`: Update mutable fields (status, suspense date, tags, priority score, etc.).

### 2.2 Assignments & Comments
- `POST /tasks/{id}/assignments`: Add routing nodes with assignee (user or org), role (`owner|coord|reviewer|approver`), due overrides, and initial state.
- `POST /tasks/{id}/comments`: Create threaded comments; optional `parent_comment_id` for replies.
- `GET /tasks/{id}/comments`: Return chronological comment threads with authorship and timestamps.

### 2.3 Agent Augmentations
- `GET /tasks/{id}/summary`: MissionMind AI worker generates situational summaries, action items, and risk highlights.
- `GET /tasks/{id}/quality-check`: Returns compliance diagnostics and formatting findings.
- `GET /tasks/{id}/authority-suggestions`: Provides ranked authorities with scope justification and confidence scores.
- `GET /tasks/{id}/risk`: Computes lateness probability, risk level (`green|amber|red`), drivers, and recommended mitigations.

### 2.4 User & Org Views
- `GET /users/me/tasks?bucket=<bucket>`: Personalized queues such as `due_this_week`, `overdue`, `at_risk`, leveraging presence and workload data.
- `GET /orgs/{id}/authorities`: Lists authority entities scoped to the organization, including grade, functional scope, and recent usage.

### 2.5 Attachments Workflow
- `POST /attachments/upload-init`: Initiates secure document upload, returning SharePoint/ETMS2 storage refs or pre-signed URLs. Follow-up upload executed against returned endpoint with classification tagging.

### 2.6 Representative Schemas

#### Task
```json
{
  "id": "T-23-001234",
  "title": "Provide training readiness summary",
  "description": "G3 to consolidate Q3 readiness data...",
  "classification": "U",
  "suspense_date": "2025-09-19",
  "originator": "HQDA DCS G-3/5/7",
  "org_unit_id": "DIV-3ID-G3",
  "priority_score": 0.86,
  "status": "in_work",
  "tags": ["readiness", "training"],
  "record_series_id": "ARIMS:RN-1-335-42",
  "attachments": [
    {"id": "A-778", "name": "Readiness_Inputs.xlsx", "classification": "U", "storage_ref": "sp://..."}
  ],
  "created_at": "2025-09-15T14:10:00Z",
  "updated_at": "2025-09-16T10:22:00Z"
}
```

#### Assignment
```json
{
  "id": "ASGN-001",
  "task_id": "T-23-001234",
  "assignee_user_id": "USR-938",
  "role": "reviewer",
  "assigned_at": "2025-09-15T15:00:00Z",
  "due_override_date": "2025-09-18",
  "state": "pending"
}
```

#### Risk
```json
{
  "task_id": "T-23-001234",
  "risk_level": "amber",
  "late_probability": 0.42,
  "drivers": [
    "Approver on leave",
    "High dependency count"
  ],
  "last_evaluated_at": "2025-09-16T11:30:00Z"
}
```

## 3. Ontology

### 3.1 Core Classes
- **Task**: Work item representing a staffed document or action; attributes include classification, suspense date, priority score, tags, record series, related tasks, and attachments.
- **Assignment**: Routing entry linking a task to an assignee (user or org) with role, due overrides, and state.
- **User**: Individual participant with name, A365 email UPN, presence, roles, skill tags, and organizational membership.
- **OrgUnit**: Structured unit (HQDA/ACOM/ASCC/DRU/Corps/Division/Brigade/Battalion) with parent-child relationships.
- **Authority**: Approval role containing title, grade (GS-15/O6/SES/GO), organizational scope, policy domains, and approval precedence.
- **Comment**: Threaded discussion nodes attached to tasks, referencing parent comments for hierarchy.
- **Suspense**: Time-bound requirement tracking suspense date, lead time, risk level, and reminder cadence.
- **Attachment**: Document metadata including mime type, storage reference, classification, and checksum.
- **AuditLog**: Immutable record of actions (create/update/route/approve) with actor, timestamp, and contextual details.
- **RecordSeries**: ARIMS classification metadata governing retention and disposition.

### 3.2 Relationships
- `Task` **hasMany** `Assignment`, `Comment`, `Attachment`, and `AuditLog` entries.
- `Assignment` **assignedTo** either `User` or `OrgUnit`; `User` **memberOf** `OrgUnit`.
- `Task` **governedBy** `RecordSeries` and **monitoredBy** `Suspense`.
- `Task` **suggestedAuthority** -> `Authority` (ranked list with confidence).
- `Authority` **scopedTo** `OrgUnit` and **precedes** lower-level authorities.
- `AuditLog` **recordsActionOn** `Task`, `Assignment`, `Comment`, `Suspense`, or `Authority`.
- `Task` **relatedTo** other `Task` objects for dependencies or parent-child taskers.

### 3.3 Derived Insights & Inference Rules
- **Priority Scoring**: `priority_score = f(urgency(suspense_date, lead_time), originator_weight, mission_keyword_boost, historical_escalation_risk, workload_balance)`.
- **Risk Assessment**: `risk_level = g(days_to_suspense, task_complexity, dependency_count, owner_history, calendar_effects)` with thresholds for green/amber/red.
- **Authority Recommendation**: Blend policy taxonomies, echelon, authority scope, and collaborative filtering on historical approvals to produce ranked candidates.
- **Comment Summarization**: Cluster comments by semantic similarity, flag nonconcurrence, and propagate decision needed indicators.
- **Predictive Staffing Insights**: Aggregate cycle times and throughput per `OrgUnit`/`User`, forecast bottlenecks, and alert when suspenses collide or approvers are unavailable.

### 3.4 Interaction Channels
- **A365 Bots**: Natural language queries such as "Show me all open taskers due this week" or "Summarize the top 3 risks flagged in current suspense reports" map to API calls with ontology-aligned responses.
- **Dashboards**: Leadership views displaying risk heatmaps, workload distribution, and authority utilization drawn from ontology relationships.
- **Automations**: MissionMind agents trigger ETMS2 updates, send reminders, and initiate draft generation using ontology-driven context.

## 4. MCP Microservice Architecture

### 4.1 Architecture Overview
The MissionMind service layer operates as a Model Context Protocol (MCP) server that mediates all agent interactions with ETMS2-adjacent capabilities. The MCP gateway exposes curated tools (task routing, authority recommendation, quality checks, summaries, risk analytics) to MissionMind agents while delegating execution to domain microservices built in Python. Each microservice encapsulates a distinct concern, scales independently, and communicates through an event backbone and shared observability layer.

### 4.2 Service Decomposition
| Service | Responsibility | Implementation Highlights |
| --- | --- | --- |
| `mcp-gateway` | Terminates MCP connections, authenticates agents, orchestrates tool calls across downstream services, and enforces policy guardrails. | Python async server implementing MCP; FastAPI adapter for REST fallbacks; integrates with Azure AD / Army 365 tokens. |
| `task-sync-service` | Synchronizes ETMS2 tasks, assignments, and attachments into MissionMind data stores; handles outbound updates back to ETMS2. | Async ETMS2 client, change-data polling, idempotent upserts into Postgres; publishes domain events. |
| `routing-service` | Computes priority scores and recommended routing destinations using classifiers and heuristics. | PyTorch/Scikit models served via FastAPI; feature store backed by Redis/Feast; Celery workers for retraining. |
| `authority-graph-service` | Maintains authority knowledge graph and answers approval-scope queries. | Neo4j or AWS Neptune driver; GraphQL/REST facade; caches frequent lookups. |
| `risk-analytics-service` | Predicts suspense risk levels and cycle time bottlenecks. | Python analytics pipelines with Pandas/Prophet; scheduled batch jobs plus on-demand scoring endpoint. |
| `llm-quality-service` | Generates task summaries, comment clustering, and draft quality checks via managed LLM endpoints. | Prompt orchestration layer (LangChain/LlamaIndex); integrates with DoD-approved LLM gateway; streaming responses to MCP. |
| `notification-service` | Sends Teams/Outlook notifications, reminder digests, and escalation alerts. | MS Graph API client, rate-limited dispatch queue, policy-aware templates. |
| `audit-compliance-service` | Aggregates audit logs, classification tags, and retention policies. | Write-ahead logging to immutable store (e.g., Azure Blob WORM); produces compliance reports. |
| Shared data platform | Provides canonical storage (Postgres), object storage (SPO/S3), and message bus (Azure Service Bus/Kafka). | Managed services with STIG hardening, encryption at rest/in transit, and role-based access controls. |

### 4.3 Interaction & Data Flow
1. MissionMind agent invokes an MCP tool (e.g., `mm.get_task_summary`). The MCP gateway authenticates the agent and emits a `ToolInvocation` event.
2. Gateway calls the corresponding domain microservice (REST/gRPC) or enqueues work on the event bus. Streaming responses are proxied back to the agent.
3. Domain services persist state changes to the shared data platform and emit `DomainEvent`s (e.g., `TaskPriorityUpdated`).
4. Notification service subscribes to relevant events to drive Teams reminders and dashboards.
5. Audit service receives append-only logs from all services, ensuring traceability and facilitating AR 25-50 / ARIMS compliance.
6. Periodic ETMS2 sync jobs reconcile authoritative records, resolving conflicts via deterministic merge rules.

### 4.4 Python Service Layer Stack (MVP Focus)
- **Frameworks**: FastAPI + Uvicorn providing a lightweight ASGI layer; `pydantic` models shared across services.
- **Data & State**: SQLite (file-backed) for persistence, `sqlmodel` or `sqlalchemy` for quick ORM mapping, and simple JSON fixtures for seeded data.
- **Async & Messaging**: Native `asyncio` tasks with in-process queues; `httpx` for ETMS2 mock integration; `APScheduler` or `asyncio.create_task` loops for periodic jobs.
- **ML/AI Tooling**: `scikit-learn` for heuristic classifiers/regressors; optional `numpy`/`pandas` for feature prep; LLM calls proxied through a single `langchain` runnable or direct REST call to a managed endpoint.
- **Security**: Stub token validation with `pyjwt` and environment-configured shared secrets (demo only) while documenting the A365 integration path.
- **Observability**: Minimal `structlog` logging to stdout, FastAPI autogenerated docs for manual verification, and `pytest` + `pytest-asyncio` for smoke tests.

### 4.5 Deployment & Operations (Demo Posture)
- Package services as Docker images and orchestrate locally with `docker compose`; each service exposes HTTP endpoints on the host network.
- Provide `.env`-driven configuration for secrets/URLs to simplify demo setup; avoid external secret managers in MVP.
- Use a single VM or laptop environment; rely on manual start scripts (`make up`, `make seed`) instead of GitOps automation.
- Capture basic health endpoints (`/healthz`) and include a reset script to reload seed data between demos.
- Document upgrade path toward production hardening (mTLS, Kubernetes, audit storage) without implementing it in the MVP.

### 4.6 Sample MCP Gateway Skeleton (Python)
```python
"""Minimal MissionMind MCP gateway exposing two tools for the MVP demo."""
import asyncio
from typing import AsyncIterator

from mcp.server import Server, Tool, ToolResult  # hypothetical MCP helper package
from missionmind.clients import etms2, insights

server = Server(name="missionmind-mcp", version="0.1.0")

@server.tool(name="mm.get_task_summary", description="Summarize a task and highlight risks.")
async def get_task_summary(task_id: str) -> ToolResult:
    task = await etms2.get_task(task_id)
    summary = await insights.generate_summary(task)
    return ToolResult(content=summary.text, metadata={"risk_level": summary.risk_level})

@server.tool(name="mm.route_task", description="Compute optimal routing for a task.")
async def route_task(task_id: str) -> ToolResult:
    task = await etms2.get_task(task_id)
    routing = await insights.compute_routing(task)
    return ToolResult(content=routing.plan, metadata={"priority_score": routing.priority})

async def main() -> None:
    await server.start(host="0.0.0.0", port=7037)
    # Keep the server alive until cancelled
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
```
_Notes_: For the MVP we assume a simplified MCP helper library and mock ETMS2 client; production would swap in the official Model Context Protocol transport, hardened auth, and full telemetry.

### 4.7 MCP Tool Mapping to REST APIs
MissionMind agents interact exclusively through MCP tool calls. Each tool wraps one or more REST endpoints from the API specification, shielding the LLM from protocol details while enforcing guardrails.

| MCP Tool | Backing REST Endpoints | Purpose for LLM |
| --- | --- | --- |
| `mm.get_task` | `GET /tasks/{id}` | Retrieve authoritative metadata before reasoning or drafting responses. |
| `mm.list_tasks` | `GET /tasks` with query filters | Let the LLM answer queries such as "show open taskers due this week" using controlled parameter templates. |
| `mm.update_task_status` | `PATCH /tasks/{id}` | Allow the agent to close or reclassify tasks after human approval workflows. |
| `mm.add_assignment` | `POST /tasks/{id}/assignments` | Route tasks to orgs/personnel as recommended by reasoning chains. |
| `mm.add_comment` | `POST /tasks/{id}/comments` | Post summarized feedback or draft responses on behalf of users. |
| `mm.fetch_comments` | `GET /tasks/{id}/comments` | Gather context prior to summarization or adjudication. |
| `mm.get_summary` | `GET /tasks/{id}/summary` | Invoke LLM-powered summaries residing in microservices; ensures consistent formatting. |
| `mm.run_quality_check` | `GET /tasks/{id}/quality-check` | Execute compliance checks and relay results back to the user. |
| `mm.suggest_authority` | `GET /tasks/{id}/authority-suggestions` | Provide ranked approver recommendations for routing decisions. |
| `mm.get_risk` | `GET /tasks/{id}/risk` | Surface suspense risk and mitigation guidance. |
| `mm.user_bucket` | `GET /users/me/tasks?bucket=<bucket>` | Serve personalized task queues in chat experiences. |

MCP tooling enforces structured input schemas (pydantic models) and validation logic, so the LLM can only issue parameterized calls that correspond to safe REST requests. The gateway manages retries, redaction of sensitive fields, and hydration of tool responses back into natural language for the agent conversation. This layering lets us evolve REST endpoints independently while exposing a stable set of MCP capabilities tailored to LLM workflows.
