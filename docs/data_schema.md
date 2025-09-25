# MissionMind Data Schema

This document captures the current MissionMind TasksMind relational schema as defined in `app/models.py`. It highlights each table's purpose, core fields, and how entities relate to one another.

## Enumerations
- **ClassificationLevel**: `UNCLASSIFIED (U)`, `CONFIDENTIAL (C)`, `SECRET (S)`, `TOP_SECRET (TS)`.
- **TaskStatus**: `DRAFT`, `OPEN`, `ASSIGNED`, `IN_WORK`, `COORDINATION`, `PENDING_SIGNATURE`, `CLOSED`, `OVERDUE`, `CANCELLED`.
- **AssignmentRole**: `OPR`, `OCR`, `INFO`, `REVIEWER`, `APPROVER`, `ACTION_OFFICER`.
- **AssignmentState**: `PENDING`, `ACCEPTED`, `IN_PROGRESS`, `COMPLETED`, `DECLINED`.
- **CoordinationType**: `CONCUR`, `NONCONCUR`, `CONCUR_WITH_COMMENT`, `NO_STAKE`.
- **RiskLevel**: `GREEN`, `AMBER`, `RED`.
- **EchelonLevel**: `HQDA`, `ACOM`, `ASCC`, `DRU`, `CORPS`, `DIVISION`, `BRIGADE`, `BATTALION`, `COMPANY`.

## Core Tables

### Task (`task`)
Military task/tasker record aligned to ETMS2 requirements.

| Field | Type | Notes |
| --- | --- | --- |
| `id` | `str` | Primary key, indexed |
| `control_number` | `str` | Unique, formatted `T-YY-XXXXXX` |
| `title` | `str` | Task title (≤200 chars) |
| `description` | `Text` | Detailed instructions |
| `originator` | `str` | Source organization/person |
| `org_unit_id` | `str` | FK → `orgunit.id` |
| `classification` | `ClassificationLevel` | Default `UNCLASSIFIED` |
| `classification_portions` | `JSON` | Portion markings by field |
| `cui_marked` | `bool` | Controlled Unclassified Information flag |
| `cui_categories` | `JSON` | CUI category codes |
| `cui_banner` | `str?` | Banner text |
| `cui_decontrol_date` | `date?` | Decontrol schedule |
| `suspense_date` | `date` | External suspense |
| `internal_suspense_date` | `date?` | Internal suspense |
| `suspense_basis` | `str?` | Supporting regulation reference |
| `priority_score` | `float` | Between 0 and 1 (check constraint) |
| `expedite_flag` | `bool` | Expedite indicator |
| `status` | `TaskStatus` | Workflow state, indexed |
| `signature_required_level` | `str?` | Required signature grade |
| `digital_signature` | `JSON` | Signature metadata |
| `record_series_id` | `str?` | ARIMS RRS-A linkage |
| `disposition_date` | `date?` | Retention disposition |
| `official_record_location` | `str?` | Archive reference |
| `created_at` | `datetime` | Indexed |
| `updated_at` | `datetime` | — |
| `created_by` | `str?` | FK → `user.id` |
| `tags` | `JSON` | Array of string tags |
| `metadata` | `JSON?` | Additional structured data |

**Relationships**
- `Task` ↔ `OrgUnit`: many tasks per org unit (`task.org_unit_id`).
- `Task` ↔ `User`: optional creator (`task.created_by`).
- `Task` ↔ `Assignment`: one-to-many (`task.assignments`, cascade delete).
- `Task` ↔ `Comment`: one-to-many (`task.comments`).
- `Task` ↔ `Attachment`: one-to-many (`task.attachments`).
- `Task` ↔ `Suspense`: one-to-one (`task.suspense`).
- `Task` ↔ `AuditLog`: filtered one-to-many for entries where `object_type='Task'`.
- **Association tables**: `task_tag_link` (task ↔ arbitrary tags), `task_related_link` (task ↔ related task).

### Assignment (`assignment`)
Tracks routing of tasks to users or organizational elements.

| Field | Type | Notes |
| --- | --- | --- |
| `id` | `int` | Primary key |
| `task_id` | `str` | FK → `task.id`, indexed |
| `assignee_type` | `str` | Either `org` or `user` |
| `assignee_user_id` | `str?` | FK → `user.id` |
| `assignee_org_id` | `str?` | FK → `orgunit.id` |
| `role` | `AssignmentRole` | Responsible role |
| `state` | `AssignmentState` | Workflow state |
| `assigned_at` | `datetime` | Timestamp |
| `due_override_date` | `date?` | Custom suspense |
| `completed_at` | `datetime?` | Completion timestamp |
| `coordination_type` | `CoordinationType?` | Response type |
| `by_name_concur` | `bool` | By-name concurrence flag |
| `rationale` | `Text?` | Coordination justification |
| `assigned_by` | `str` | FK → `user.id` |

**Relationships**
- `Assignment` ↔ `Task`: many assignments per task.
- `Assignment` ↔ `User`: optional assignee (`assignee_user`), required assigner (`assigned_by`), optional coordinator.
- `Assignment` ↔ `OrgUnit`: optional organizational assignee.
- Check constraint enforces either user or org assignee.

### User (`user`)
Army 365-linked user account.

| Field | Type | Notes |
| --- | --- | --- |
| `id` | `str` | Primary key |
| `upn` | `str` | Unique UPN/email |
| `name` | `str` | Display name |
| `rank_grade` | `str?` | Rank or grade |
| `org_unit_id` | `str` | FK → `orgunit.id`, indexed |
| `phone` | `str?` | — |
| `office_symbol` | `str?` | — |
| `roles` | `JSON` | Role identifiers |
| `skill_tags` | `JSON` | Skill keywords |
| `clearance_level` | `ClassificationLevel?` | Max clearance |
| `is_available` | `bool` | Availability flag |
| `out_of_office_until` | `date?` | OOO end |
| `created_at` | `datetime` | — |
| `last_login` | `datetime?` | — |

**Relationships**
- `User` ↔ `OrgUnit`: many users per org unit.
- Referenced by tasks (`created_by`), assignments (`assignee_user_id`, `assigned_by`), attachments (`uploaded_by`), comments (`author_user_id`), suspense extensions, audit logs.

### OrgUnit (`orgunit`)
Represents the military unit hierarchy.

| Field | Type | Notes |
| --- | --- | --- |
| `id` | `str` | Primary key |
| `name` | `str` | Indexed |
| `short_name` | `str?` | — |
| `echelon` | `EchelonLevel` | Organizational tier |
| `parent_id` | `str?` | Self-FK → `orgunit.id` |
| `uic` | `str?` | Unique UIC |
| `address` | `str?` | — |
| `timezone` | `str` | Default `America/New_York` |
| `active` | `bool` | Status |
| `created_at` | `datetime` | — |

**Relationships**
- Hierarchical parent (`parent`) and implicit children via `parent_id`.
- `OrgUnit` ↔ `User`: one-to-many.
- `OrgUnit` ↔ `Authority`: one-to-many.
- Referenced by tasks (`org_unit_id`) and assignments (`assignee_org_id`).

### Authority (`authority`)
Defines approval authorities tied to organizational units.

| Field | Type | Notes |
| --- | --- | --- |
| `id` | `str` | Primary key |
| `title` | `str` | Authority name |
| `org_unit_id` | `str` | FK → `orgunit.id`, indexed |
| `grade` | `str` | Grade (GS-15/O6/etc.) |
| `position_title` | `str?` | — |
| `authority_scope` | `JSON` | Authorized domains |
| `policy_areas` | `JSON` | Policy coverage |
| `can_delegate` | `bool` | Delegation allowed |
| `delegation_limit` | `str?` | Delegation bounds |
| `precedence_order` | `int` | Lower = higher precedence |
| `current_incumbent` | `str?` | FK → `user.id` |
| `active` | `bool` | Status |

**Relationships**
- `Authority` ↔ `OrgUnit`: many authorities per unit.
- `Authority` ↔ `User`: optional incumbent assignment.

### Comment (`comment`)
Threaded commentary on tasks.

| Field | Type | Notes |
| --- | --- | --- |
| `id` | `int` | Primary key |
| `task_id` | `str` | FK → `task.id`, indexed |
| `author_user_id` | `str` | FK → `user.id` |
| `body` | `Text` | Comment text |
| `parent_comment_id` | `int?` | Self-FK for threading |
| `created_at` | `datetime` | Indexed |
| `edited_at` | `datetime?` | — |
| `is_decision` | `bool` | Marks adjudication comments |
| `classification` | `ClassificationLevel` | Default `UNCLASSIFIED` |

**Relationships**
- `Comment` ↔ `Task`: many comments per task.
- `Comment` ↔ `User`: many comments per author.
- Self-referential parent/child threads.

### Attachment (`attachment`)
Stores metadata for task documents.

| Field | Type | Notes |
| --- | --- | --- |
| `id` | `str` | Primary key |
| `task_id` | `str` | FK → `task.id`, indexed |
| `filename` | `str` | Original name |
| `mime_type` | `str` | Content type |
| `size_bytes` | `int` | File size |
| `checksum` | `str?` | SHA-256 hash |
| `storage_ref` | `str` | SharePoint/S3 pointer |
| `storage_type` | `str` | Default `sharepoint` |
| `classification` | `ClassificationLevel` | — |
| `cui_marked` | `bool` | CUI flag |
| `uploaded_by` | `str` | FK → `user.id` |
| `uploaded_at` | `datetime` | Timestamp |
| `record_series_id` | `str?` | ARIMS linkage |

**Relationships**
- `Attachment` ↔ `Task`: many attachments per task.
- `Attachment` ↔ `User`: many attachments per uploader.

### Suspense (`suspense`)
Per-task suspense management.

| Field | Type | Notes |
| --- | --- | --- |
| `id` | `int` | Primary key |
| `task_id` | `str` | Unique FK → `task.id`, indexed |
| `suspense_date` | `date` | Current suspense |
| `lead_time_days` | `int` | Reminder lead time |
| `risk_level` | `RiskLevel` | Late-risk indicator |
| `late_probability` | `float` | 0–1 probability |
| `risk_drivers` | `JSON` | Risk factors |
| `reminder_sent_dates` | `JSON` | Reminder timestamps |
| `escalation_sent` | `bool` | Escalation flag |
| `extension_count` | `int` | Number of extensions |
| `original_suspense_date` | `date` | First suspense |
| `last_evaluated_at` | `datetime` | Last risk evaluation |

**Relationships**
- `Suspense` ↔ `Task`: exactly one suspense per task.
- `Suspense` ↔ `ExtensionRequest`: one-to-many.

### ExtensionRequest (`extension_request`)
Requests to extend a suspense.

| Field | Type | Notes |
| --- | --- | --- |
| `id` | `int` | Primary key |
| `suspense_id` | `int` | FK → `suspense.id`, indexed |
| `requested_by` | `str` | FK → `user.id` |
| `justification` | `Text` | Rationale |
| `new_suspense_date` | `date` | Proposed date |
| `approved` | `bool?` | Approval decision |
| `approved_by` | `str?` | FK → `user.id` |
| `decision_comment` | `str?` | Decision notes |
| `requested_at` | `datetime` | Submission timestamp |
| `decision_at` | `datetime?` | Decision timestamp |

**Relationships**
- `ExtensionRequest` ↔ `Suspense`: many requests per suspense.
- `ExtensionRequest` ↔ `User`: requester and optional approver.

### RecordSeries (`record_series`)
ARIMS record retention catalog.

| Field | Type | Notes |
| --- | --- | --- |
| `id` | `str` | Primary key |
| `series_number` | `str` | Unique RRS-A code |
| `title` | `str` | Record series title |
| `retention_years` | `int` | Retention duration |
| `disposition_action` | `str` | Destroy / permanent / review |
| `description` | `Text?` | Narrative description |
| `active` | `bool` | Status |

**Relationships**
- Optionally referenced by tasks or attachments via `record_series_id`.

### AuditLog (`audit_log`)
Immutable event history for key objects.

| Field | Type | Notes |
| --- | --- | --- |
| `id` | `int` | Primary key |
| `object_type` | `str` | Target type (e.g., `Task`) |
| `object_id` | `str` | Target identifier |
| `actor_user_id` | `str` | FK → `user.id`, indexed |
| `action` | `str` | Action verb |
| `details` | `JSON` | Change payload |
| `ip_address` | `str?` | — |
| `user_agent` | `str?` | — |
| `ts` | `datetime` | Timestamp, indexed |

**Relationships**
- `AuditLog` ↔ `User`: many audit entries per actor.
- Configured view-only link to `Task` when `object_type='Task'`.

## Association Tables (No ORM class)
- **`task_tag_link`**: bridges `task.id` with free-form tag values (`tag`). Enables additional many-to-many tagging beyond the embedded JSON `tags` list.
- **`task_related_link`**: self-referential bridge that links `task.id` to `task.id` for related task cross-references. Cascade deletes ensure dependent links are removed with their parent tasks.

## Relationship Overview
- Tasks sit at the center of the schema, connecting to assignments, comments, attachments, suspense, and audit logs.
- Organizational hierarchy (`orgunit`) underpins user membership, task ownership, authority definitions, and organizational assignments.
- Suspense management (`suspense`, `extension_request`) extends task timelines with risk tracking and approvals.
- Audit logging captures user actions across objects, ensuring traceability for compliance.
