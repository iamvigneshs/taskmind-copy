# MissionMind API Specification

This specification documents the MissionMind TasksMind REST API surface available in the current codebase. Routes are mounted beneath the `/tasks` prefix and rely on a shared SQLModel session dependency.

- **Base URL**: `/tasks`
- **Content Type**: `application/json`
- **Authentication**: Not yet implemented in this code snapshot (assumed to rely on future middleware).

## Common Conventions
- All timestamps use ISO 8601 in UTC.
- Enum values are lowercase strings unless otherwise noted.
- Error responses follow FastAPI's default error envelope: `{ "detail": "..." }` with relevant HTTP status codes (e.g., 404 when a task is not found).

## Schemas Overview

### TaskCreate
Fields for creating a new task.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | `string` | No | Optional override; defaults to generated `T-25-XXXXXX` sequence. |
| `title` | `string` | Yes | Task title. |
| `description` | `string` | Yes | Full task description. |
| `classification` | `string` | Yes | Security classification (e.g., `U`, `C`, `S`, `TS`). |
| `suspense_date` | `date` | Yes | External suspense date. |
| `originator` | `string` | Yes | Originating organization. |
| `org_unit_id` | `string` | Yes | Identifier of owning org unit. |
| `record_series_id` | `string` | No | ARIMS series linkage. |
| `tags` | `array[string]` | No | Keyword tags. |

### TaskUpdate
Fields that can be patched on an existing task. Omitted fields remain unchanged.

| Field | Type | Notes |
| --- | --- | --- |
| `title` | `string` | Optional. |
| `description` | `string` | Optional. |
| `classification` | `string` | Optional. |
| `suspense_date` | `date` | Optional. |
| `originator` | `string` | Optional. |
| `org_unit_id` | `string` | Optional. |
| `record_series_id` | `string` | Optional. |
| `status` | `string` | Optional. |
| `tags` | `array[string]` | Optional replacement of tag set. |

### TaskRead
Returned representation of a task.

| Field | Type | Notes |
| --- | --- | --- |
| `id` | `string` | Task identifier. |
| `title` | `string` | — |
| `description` | `string` | — |
| `classification` | `string` | Security marking. |
| `suspense_date` | `date` | — |
| `originator` | `string` | — |
| `org_unit_id` | `string` | — |
| `record_series_id` | `string` | Nullable. |
| `tags` | `array[string]` | — |
| `priority_score` | `number` | Computed 0–1 priority. |
| `status` | `string` | Current workflow state. |
| `created_at` | `datetime` | Creation timestamp. |
| `updated_at` | `datetime` | Last update timestamp. |
| `assignments` | `array[AssignmentRead]` | Associated routing records. |

### AssignmentCreate / AssignmentRead
Input and output payloads for assignments.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `assignee_type` | `string` | No | Defaults to `org`. Should be `org` or `user`. |
| `assignee_id` | `string` | Yes | Target org or user identifier. |
| `role` | `string` | Yes | Role per `AssignmentRole`. |
| `due_override_date` | `date` | No | Custom due date. |
| `state` | `string` | No | Defaults to `pending`. |
| `rationale` | `string` | No | Coordination notes. |

Additional fields in AssignmentRead:

| Field | Type | Notes |
| --- | --- | --- |
| `id` | `integer` | Assignment identifier. |
| `task_id` | `string` | Parent task identifier. |
| `created_at` | `datetime` | Creation timestamp. |

### CommentCreate / CommentRead

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `author_user_id` | `string` | Yes | Author identifier. |
| `body` | `string` | Yes | Comment content. |
| `parent_comment_id` | `integer` | No | Enables threaded replies. |

CommentRead adds:

| Field | Type | Notes |
| --- | --- | --- |
| `id` | `integer` | Comment identifier. |
| `task_id` | `string` | Parent task. |
| `created_at` | `datetime` | Timestamp. |

### TaskSummary

| Field | Type | Notes |
| --- | --- | --- |
| `summary` | `string` | Generated synopsis. |
| `risk_level` | `string` | Qualitative risk label. |
| `key_points` | `array[string]` | Highlights extracted by summarizer. |

### AuthoritySuggestion

| Field | Type | Notes |
| --- | --- | --- |
| `authority_id` | `string` | Suggested authority identifier. |
| `title` | `string` | Authority name. |
| `org_unit_id` | `string` | Owning organization. |
| `grade` | `string` | Grade/level. |
| `confidence` | `number` | 0–1 relevance score. |
| `rationale` | `string` | Reason for suggestion. |

### RiskInsight

| Field | Type | Notes |
| --- | --- | --- |
| `task_id` | `string` | Referenced task. |
| `risk_level` | `string` | `green`, `amber`, or `red`. |
| `late_probability` | `number` | Probability estimate (0–1). |
| `drivers` | `array[string]` | Drivers behind risk score. |
| `recommended_actions` | `array[string]` | Suggested mitigations. |

### QualityCheckResult

| Field | Type | Notes |
| --- | --- | --- |
| `task_id` | `string` | Target task. |
| `issues` | `array[QualityIssue]` | Issues flagged by automated check. |
| `passed` | `boolean` | Indicates whether medium-severity issues were found. |

QualityIssue structure:

| Field | Type | Notes |
| --- | --- | --- |
| `code` | `string` | Issue identifier. |
| `severity` | `string` | Low/medium severity levels currently used. |
| `message` | `string` | Human-readable description. |

## Endpoints

### Create Task
- **Method**: `POST`
- **Path**: `/tasks/`
- **Request Body**: `TaskCreate`
- **Success Response**: `201 Created` with `TaskRead` payload
- **Behavior**: Generates task ID when absent, computes priority score, opens task, adds default assignment via routing service.
- **Errors**: `400` on validation failure.

### List Tasks
- **Method**: `GET`
- **Path**: `/tasks/`
- **Query Parameters**:
  - `status` (`string`, optional): Filter by task status.
  - `due_before` (`datetime`, optional): ISO timestamp; tasks with suspense date on/before the provided date.
  - `org` (`string`, optional): Filter by owning org unit.
- **Success Response**: `200 OK` with `array[TaskRead]`
- **Behavior**: Applies filters when provided; always returns assignments embedded.

### Retrieve Task
- **Method**: `GET`
- **Path**: `/tasks/{task_id}`
- **Path Parameters**:
  - `task_id` (`string`): Identifier such as `T-25-000123`.
- **Success Response**: `200 OK` with `TaskRead`
- **Errors**: `404` if the task does not exist.

### Update Task
- **Method**: `PATCH`
- **Path**: `/tasks/{task_id}`
- **Request Body**: `TaskUpdate` (partial updates allowed)
- **Success Response**: `200 OK` with updated `TaskRead`
- **Behavior**: Recomputes priority score and `updated_at` field after applying changes.
- **Errors**: `404` if the task does not exist.

### Add Assignment
- **Method**: `POST`
- **Path**: `/tasks/{task_id}/assignments`
- **Request Body**: `AssignmentCreate`
- **Success Response**: `201 Created` with `AssignmentRead`
- **Behavior**: Validates parent task existence before adding.
- **Errors**: `404` if task missing.

### Add Comment
- **Method**: `POST`
- **Path**: `/tasks/{task_id}/comments`
- **Request Body**: `CommentCreate`
- **Success Response**: `201 Created` with `CommentRead`
- **Errors**: `404` if task missing.

### List Comments
- **Method**: `GET`
- **Path**: `/tasks/{task_id}/comments`
- **Success Response**: `200 OK` with `array[CommentRead]`
- **Errors**: `404` if task missing.

### Get Task Summary
- **Method**: `GET`
- **Path**: `/tasks/{task_id}/summary`
- **Success Response**: `200 OK` with `TaskSummary`
- **Behavior**: Uses summarizer service to compile description and comment highlights.
- **Errors**: `404` if task missing.

### Get Authority Suggestions
- **Method**: `GET`
- **Path**: `/tasks/{task_id}/authority-suggestions`
- **Success Response**: `200 OK` with `array[AuthoritySuggestion]`
- **Behavior**: Delegates to authority recommendation service.
- **Errors**: `404` if task missing.

### Get Risk Insight
- **Method**: `GET`
- **Path**: `/tasks/{task_id}/risk`
- **Success Response**: `200 OK` with `RiskInsight`
- **Behavior**: Computes qualitative risk based on priority score and status heuristics.
- **Errors**: `404` if task missing.

### Run Quality Check
- **Method**: `GET`
- **Path**: `/tasks/{task_id}/quality-check`
- **Success Response**: `200 OK` with `QualityCheckResult`
- **Behavior**: Executes basic content checks (description length, ARIMS linkage).
- **Errors**: `404` if task missing.

## Future Considerations
- Authentication/authorization and role enforcement should be layered before production deployment.
- Additional endpoints (e.g., for org units, authorities, users) may be defined as the service surface expands.
