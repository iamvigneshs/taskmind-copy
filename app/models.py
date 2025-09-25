# Copyright (c) 2025 Acarin Inc. All rights reserved.
# Proprietary and confidential.
"""SQLModel ORM models for MissionMind TasksMind - Military-compliant task management."""
from __future__ import annotations

from datetime import datetime, date
from typing import List, Optional, Dict
from enum import Enum

from sqlalchemy import Column, JSON, String, Index, CheckConstraint, UniqueConstraint, Text, Float, Boolean, ForeignKey, Table
from sqlmodel import Field, Relationship, SQLModel


# Enums for military compliance
class ClassificationLevel(str, Enum):
    """Security classification levels per DoDM 5200.01"""
    UNCLASSIFIED = "U"
    CONFIDENTIAL = "C"
    SECRET = "S"
    TOP_SECRET = "TS"


class TaskStatus(str, Enum):
    """Task lifecycle states"""
    DRAFT = "draft"
    OPEN = "open"
    ASSIGNED = "assigned"
    IN_WORK = "in_work"
    COORDINATION = "coord"
    PENDING_SIGNATURE = "pending_signature"
    CLOSED = "closed"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class AssignmentRole(str, Enum):
    """Assignment roles per DoDM 5110.04"""
    OPR = "opr"  # Office of Primary Responsibility
    OCR = "ocr"  # Office of Collateral Responsibility
    INFO = "info"  # Information only
    REVIEWER = "reviewer"
    APPROVER = "approver"
    ACTION_OFFICER = "action_officer"


class AssignmentState(str, Enum):
    """Assignment workflow states"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DECLINED = "declined"


class CoordinationType(str, Enum):
    """Coordination response types"""
    CONCUR = "concur"
    NONCONCUR = "nonconcur"
    CONCUR_WITH_COMMENT = "concur_with_comment"
    NO_STAKE = "no_stake"


class RiskLevel(str, Enum):
    """Risk assessment levels"""
    GREEN = "green"
    AMBER = "amber"
    RED = "red"


class EchelonLevel(str, Enum):
    """Military organizational echelons"""
    HQDA = "HQDA"
    ACOM = "ACOM"  # Army Command
    ASCC = "ASCC"  # Army Service Component Command
    DRU = "DRU"    # Direct Reporting Unit
    CORPS = "CORPS"
    DIVISION = "DIVISION"
    BRIGADE = "BRIGADE"
    BATTALION = "BATTALION"
    COMPANY = "COMPANY"


# Association tables
task_tag_link = Table(
    "task_tag_link",
    SQLModel.metadata,
    Column("task_id", String, ForeignKey("task.id", ondelete="CASCADE")),
    Column("tag", String),
)

task_related_link = Table(
    "task_related_link",
    SQLModel.metadata,
    Column("task_id", String, ForeignKey("task.id", ondelete="CASCADE")),
    Column("related_task_id", String, ForeignKey("task.id", ondelete="CASCADE")),
)


class Task(SQLModel, table=True):
    """Military task/tasker with ETMS2 compliance"""
    __tablename__ = "task"
    
    # Primary identification
    id: Optional[str] = Field(default=None, primary_key=True, index=True)
    control_number: str = Field(unique=True, index=True, regex="^T-\\d{2}-\\d{6}$")  # T-YY-XXXXXX format
    
    # Core task information
    title: str = Field(max_length=200)
    description: Text = Field(sa_column=Column(Text))
    originator: str = Field(index=True)  # HQDA/OSD/CCA/External entity
    org_unit_id: str = Field(foreign_key="orgunit.id", index=True)
    
    # Classification and CUI per DoDM 5200.01 and DoDI 5200.48
    classification: ClassificationLevel = Field(default=ClassificationLevel.UNCLASSIFIED)
    classification_portions: Optional[Dict[str, str]] = Field(default=None, sa_column=Column(JSON))
    cui_marked: bool = Field(default=False)
    cui_categories: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    cui_banner: Optional[str] = None
    cui_decontrol_date: Optional[date] = None
    
    # Timing and prioritization
    suspense_date: date = Field(index=True)
    internal_suspense_date: Optional[date] = None  # Earlier internal deadline
    suspense_basis: Optional[str] = None  # Reference to Table 1 standard times
    priority_score: float = Field(default=0.0, ge=0.0, le=1.0)
    expedite_flag: bool = Field(default=False)
    
    # Status and workflow
    status: TaskStatus = Field(default=TaskStatus.DRAFT, index=True)
    signature_required_level: Optional[str] = None  # GO/SES/O6/GS15
    digital_signature: Optional[Dict[str, str]] = Field(default=None, sa_column=Column(JSON))
    
    # Records management per AR 25-400-2
    record_series_id: Optional[str] = Field(index=True)  # ARIMS RRS-A series
    disposition_date: Optional[date] = None
    official_record_location: Optional[str] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = Field(foreign_key="user.id")
    
    # JSON fields for flexibility
    tags: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    metadata: Optional[Dict] = Field(default=None, sa_column=Column(JSON))
    
    # Relationships
    assignments: List["Assignment"] = Relationship(back_populates="task", cascade_delete=True)
    comments: List["Comment"] = Relationship(back_populates="task", cascade_delete=True)
    attachments: List["Attachment"] = Relationship(back_populates="task", cascade_delete=True)
    suspense: Optional["Suspense"] = Relationship(back_populates="task", cascade_delete=True)
    audit_logs: List["AuditLog"] = Relationship(
        back_populates="task",
        sa_relationship_kwargs={"primaryjoin": "and_(Task.id==AuditLog.object_id, AuditLog.object_type=='Task')"}
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint("priority_score >= 0 AND priority_score <= 1"),
        Index("idx_task_suspense_status", "suspense_date", "status"),
        Index("idx_task_org_status", "org_unit_id", "status"),
    )


class Assignment(SQLModel, table=True):
    """Task routing and assignment tracking"""
    __tablename__ = "assignment"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: str = Field(foreign_key="task.id", index=True)
    
    # Assignee can be user or org
    assignee_type: str = Field(default="org")  # "org" or "user"
    assignee_user_id: Optional[str] = Field(foreign_key="user.id", default=None)
    assignee_org_id: Optional[str] = Field(foreign_key="orgunit.id", default=None)
    
    # Role and workflow
    role: AssignmentRole
    state: AssignmentState = Field(default=AssignmentState.PENDING)
    
    # Timing
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    due_override_date: Optional[date] = None
    completed_at: Optional[datetime] = None
    
    # Coordination response
    coordination_type: Optional[CoordinationType] = None
    by_name_concur: bool = Field(default=False)
    rationale: Optional[Text] = Field(default=None, sa_column=Column(Text))
    
    # Tracking
    assigned_by: str = Field(foreign_key="user.id")
    
    # Relationships
    task: Optional[Task] = Relationship(back_populates="assignments")
    assignee_user: Optional["User"] = Relationship(foreign_keys=[assignee_user_id])
    assignee_org: Optional["OrgUnit"] = Relationship(foreign_keys=[assignee_org_id])
    
    __table_args__ = (
        CheckConstraint("(assignee_user_id IS NOT NULL) OR (assignee_org_id IS NOT NULL)"),
        Index("idx_assignment_task_role", "task_id", "role"),
        Index("idx_assignment_state", "state"),
    )


class User(SQLModel, table=True):
    """User account with Army 365 integration"""
    __tablename__ = "user"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    upn: str = Field(unique=True, index=True)  # Army365 email/UPN
    name: str
    rank_grade: Optional[str] = None  # Military rank or civilian grade
    
    # Organization and contact
    org_unit_id: str = Field(foreign_key="orgunit.id", index=True)
    phone: Optional[str] = None
    office_symbol: Optional[str] = None
    
    # Permissions and skills
    roles: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    skill_tags: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    clearance_level: Optional[ClassificationLevel] = None
    
    # Availability
    is_available: bool = Field(default=True)
    out_of_office_until: Optional[date] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    
    # Relationships
    org_unit: Optional["OrgUnit"] = Relationship(back_populates="users")


class OrgUnit(SQLModel, table=True):
    """Military organizational unit hierarchy"""
    __tablename__ = "orgunit"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    short_name: Optional[str] = None
    echelon: EchelonLevel
    
    # Hierarchy
    parent_id: Optional[str] = Field(foreign_key="orgunit.id", default=None)
    
    # Command structure
    uic: Optional[str] = Field(unique=True, default=None)  # Unit Identification Code
    address: Optional[str] = None
    timezone: str = Field(default="America/New_York")
    
    # Metadata
    active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    users: List["User"] = Relationship(back_populates="org_unit")
    authorities: List["Authority"] = Relationship(back_populates="org_unit")
    parent: Optional["OrgUnit"] = Relationship(
        sa_relationship_kwargs={"remote_side": "OrgUnit.id"}
    )
    
    __table_args__ = (
        Index("idx_orgunit_echelon", "echelon"),
        Index("idx_orgunit_parent", "parent_id"),
    )


class Authority(SQLModel, table=True):
    """Approval authority definitions"""
    __tablename__ = "authority"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    title: str
    org_unit_id: str = Field(foreign_key="orgunit.id", index=True)
    
    # Authority level
    grade: str  # GS-15/O6/SES/GO
    position_title: Optional[str] = None
    
    # Scope of authority
    authority_scope: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    policy_areas: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    
    # Delegation
    can_delegate: bool = Field(default=True)
    delegation_limit: Optional[str] = None
    precedence_order: int = Field(default=100)  # Lower number = higher precedence
    
    # Availability
    current_incumbent: Optional[str] = Field(foreign_key="user.id", default=None)
    active: bool = Field(default=True)
    
    # Relationships
    org_unit: Optional["OrgUnit"] = Relationship(back_populates="authorities")
    incumbent: Optional["User"] = Relationship(foreign_keys=[current_incumbent])
    
    __table_args__ = (
        Index("idx_authority_precedence", "precedence_order"),
        Index("idx_authority_active", "active"),
    )


class Comment(SQLModel, table=True):
    """Threaded comments on tasks"""
    __tablename__ = "comment"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: str = Field(foreign_key="task.id", index=True)
    
    # Author and content
    author_user_id: str = Field(foreign_key="user.id")
    body: Text = Field(sa_column=Column(Text))
    
    # Threading
    parent_comment_id: Optional[int] = Field(foreign_key="comment.id", default=None)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    edited_at: Optional[datetime] = None
    is_decision: bool = Field(default=False)  # Marks adjudication comments
    
    # Classification
    classification: ClassificationLevel = Field(default=ClassificationLevel.UNCLASSIFIED)
    
    # Relationships
    task: Optional[Task] = Relationship(back_populates="comments")
    author: Optional["User"] = Relationship(foreign_keys=[author_user_id])
    parent: Optional["Comment"] = Relationship(
        sa_relationship_kwargs={"remote_side": "Comment.id"}
    )
    
    __table_args__ = (
        Index("idx_comment_task_created", "task_id", "created_at"),
    )


class Attachment(SQLModel, table=True):
    """Document attachments with classification"""
    __tablename__ = "attachment"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    task_id: str = Field(foreign_key="task.id", index=True)
    
    # File information
    filename: str
    mime_type: str
    size_bytes: int
    checksum: Optional[str] = None  # SHA-256 hash
    
    # Storage
    storage_ref: str  # SharePoint/S3 reference
    storage_type: str = Field(default="sharepoint")
    
    # Classification and CUI
    classification: ClassificationLevel = Field(default=ClassificationLevel.UNCLASSIFIED)
    cui_marked: bool = Field(default=False)
    
    # Metadata
    uploaded_by: str = Field(foreign_key="user.id")
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    
    # ARIMS
    record_series_id: Optional[str] = None
    
    # Relationships
    task: Optional[Task] = Relationship(back_populates="attachments")
    uploader: Optional["User"] = Relationship(foreign_keys=[uploaded_by])


class Suspense(SQLModel, table=True):
    """Suspense tracking and reminders"""
    __tablename__ = "suspense"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: str = Field(foreign_key="task.id", unique=True, index=True)
    
    # Timing
    suspense_date: date
    lead_time_days: int = Field(default=3)
    
    # Risk assessment
    risk_level: RiskLevel = Field(default=RiskLevel.GREEN)
    late_probability: float = Field(default=0.0, ge=0.0, le=1.0)
    risk_drivers: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    
    # Reminders
    reminder_sent_dates: List[datetime] = Field(default_factory=list, sa_column=Column(JSON))
    escalation_sent: bool = Field(default=False)
    
    # Extensions
    extension_count: int = Field(default=0)
    original_suspense_date: date
    
    # Metadata
    last_evaluated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    task: Optional[Task] = Relationship(back_populates="suspense")
    extensions: List["ExtensionRequest"] = Relationship(back_populates="suspense")
    
    __table_args__ = (
        CheckConstraint("late_probability >= 0 AND late_probability <= 1"),
        Index("idx_suspense_risk", "risk_level"),
    )


class ExtensionRequest(SQLModel, table=True):
    """Suspense extension requests"""
    __tablename__ = "extension_request"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    suspense_id: int = Field(foreign_key="suspense.id", index=True)
    
    # Request details
    requested_by: str = Field(foreign_key="user.id")
    justification: Text = Field(sa_column=Column(Text))
    new_suspense_date: date
    
    # Approval
    approved: Optional[bool] = None
    approved_by: Optional[str] = Field(foreign_key="user.id", default=None)
    decision_comment: Optional[str] = None
    
    # Timestamps
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    decision_at: Optional[datetime] = None
    
    # Relationships
    suspense: Optional[Suspense] = Relationship(back_populates="extensions")
    requester: Optional["User"] = Relationship(foreign_keys=[requested_by])
    approver: Optional["User"] = Relationship(foreign_keys=[approved_by])


class RecordSeries(SQLModel, table=True):
    """ARIMS record series for retention"""
    __tablename__ = "record_series"
    
    id: Optional[str] = Field(default=None, primary_key=True)
    series_number: str = Field(unique=True)  # RRS-A number
    title: str
    
    # Retention rules
    retention_years: int
    disposition_action: str  # "destroy", "permanent", "review"
    
    # Metadata
    description: Optional[Text] = Field(default=None, sa_column=Column(Text))
    active: bool = Field(default=True)
    
    __table_args__ = (
        Index("idx_record_series_active", "active"),
    )


class AuditLog(SQLModel, table=True):
    """Immutable audit trail"""
    __tablename__ = "audit_log"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Target object
    object_type: str = Field(index=True)  # "Task", "Assignment", etc.
    object_id: str = Field(index=True)
    
    # Action details
    actor_user_id: str = Field(foreign_key="user.id", index=True)
    action: str  # "create", "update", "assign", "approve", etc.
    
    # Change details
    details: Dict = Field(default_factory=dict, sa_column=Column(JSON))
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    # Timestamp
    ts: datetime = Field(default_factory=datetime.utcnow, index=True)
    
    # Relationships
    actor: Optional["User"] = Relationship(foreign_keys=[actor_user_id])
    task: Optional["Task"] = Relationship(
        back_populates="audit_logs",
        sa_relationship_kwargs={
            "primaryjoin": "and_(Task.id==AuditLog.object_id, AuditLog.object_type=='Task')",
            "viewonly": True
        }
    )
    
    __table_args__ = (
        Index("idx_audit_log_ts", "ts"),
        Index("idx_audit_log_object", "object_type", "object_id"),
    )