# Copyright (c) 2025 Acarin Inc. All rights reserved.
# Proprietary and confidential.
"""Multi-tenant SQLModel ORM models for MissionMind TasksMind."""
from __future__ import annotations

from datetime import datetime, date
from typing import List, Optional, Dict, TYPE_CHECKING
from enum import Enum
from uuid import uuid4

from sqlalchemy import Column, JSON, String, Index, CheckConstraint, UniqueConstraint, Text, Float, Boolean, ForeignKey, Table, DateTime
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from sqlalchemy.orm import RelationshipProperty


# Enums
class TenantType(str, Enum):
    """Types of tenant organizations"""
    MILITARY = "military"
    GOVERNMENT = "government" 
    CONTRACTOR = "contractor"
    ALLIED = "allied"
    ENTERPRISE = "enterprise"  # Large corporations
    SMALL_BUSINESS = "small_business"  # Small to medium businesses
    NONPROFIT = "nonprofit"  # NGOs, nonprofits
    STARTUP = "startup"  # Startup companies
    CONSULTING = "consulting"  # Consulting firms
    HEALTHCARE = "healthcare"  # Healthcare organizations
    EDUCATION = "education"  # Schools, universities
    LEGAL = "legal"  # Law firms
    FINANCIAL = "financial"  # Banks, financial services
    TECHNOLOGY = "technology"  # Tech companies


class TenantStatus(str, Enum):
    """Tenant account status"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    PENDING = "pending"
    INACTIVE = "inactive"


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
    """Organizational levels - flexible for different org types"""
    # Military levels
    HQDA = "HQDA"
    ACOM = "ACOM"  # Army Command
    ASCC = "ASCC"  # Army Service Component Command
    DRU = "DRU"    # Direct Reporting Unit
    CORPS = "CORPS"
    DIVISION = "DIVISION"
    BRIGADE = "BRIGADE"
    BATTALION = "BATTALION"
    COMPANY = "COMPANY"
    PLATOON = "PLATOON"
    SQUAD = "SQUAD"
    
    # Corporate levels
    CORPORATE = "CORPORATE"  # Corporate HQ
    BUSINESS_UNIT = "BUSINESS_UNIT"  # Business unit/division
    REGION = "REGION"  # Regional office
    BRANCH = "BRANCH"  # Branch office
    DEPARTMENT = "DEPARTMENT"  # Department
    TEAM = "TEAM"  # Team
    
    # Generic levels
    LEVEL_1 = "LEVEL_1"  # Top level
    LEVEL_2 = "LEVEL_2"  # Second level
    LEVEL_3 = "LEVEL_3"  # Third level
    LEVEL_4 = "LEVEL_4"  # Fourth level
    LEVEL_5 = "LEVEL_5"  # Fifth level


# Base model with tenant support
class TenantBase(SQLModel):
    """Base model with tenant_id for multi-tenancy"""
    tenant_id: str = Field(foreign_key="tenant.id", index=True)


# Primary Models
class Tenant(SQLModel, table=True):
    """Multi-tenant organization - supports military, government, and commercial entities"""
    __tablename__ = "tenant"
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    name: str = Field(unique=True, index=True)
    display_name: str
    
    # Organization info
    tenant_type: TenantType = Field(default=TenantType.SMALL_BUSINESS)
    organization_code: Optional[str] = Field(unique=True, default=None)
    
    # Business details
    industry: Optional[str] = Field(default=None)  # e.g., "Technology", "Healthcare"
    country: str = Field(default="US")
    timezone: str = Field(default="America/New_York")
    company_size: Optional[str] = Field(default=None)  # "1-10", "11-50", "51-200", etc.
    
    # Contact information
    primary_contact_name: Optional[str] = None
    primary_contact_email: Optional[str] = None
    primary_contact_phone: Optional[str] = None
    billing_address: Optional[Dict] = Field(default=None, sa_column=Column(JSON))
    
    # Configuration
    status: TenantStatus = Field(default=TenantStatus.PENDING)
    max_users: int = Field(default=50)  # Default lower for small business
    max_storage_gb: int = Field(default=25)  # Default lower for small business
    
    # Security - flexible based on org type
    allowed_classification_levels: List[ClassificationLevel] = Field(
        default_factory=lambda: [ClassificationLevel.UNCLASSIFIED],
        sa_column=Column(JSON)
    )
    require_mfa: bool = Field(default=False)  # Optional for small business
    
    # Workflow settings
    approval_workflows: Dict = Field(default_factory=dict, sa_column=Column(JSON))
    task_templates: List[Dict] = Field(default_factory=list, sa_column=Column(JSON))
    
    # Customization
    branding: Optional[Dict] = Field(default=None, sa_column=Column(JSON))
    settings: Dict = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Feature flags
    features_enabled: List[str] = Field(
        default_factory=lambda: ["basic_tasks", "basic_reporting"],
        sa_column=Column(JSON)
    )
    
    # Subscription/billing
    plan: str = Field(default="basic")  # "basic", "professional", "enterprise"
    subscription_start: Optional[date] = None
    subscription_end: Optional[date] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    activated_at: Optional[datetime] = None
    
    # Relationships
    users: List["User"] = Relationship(back_populates="tenant")
    org_units: List["OrgUnit"] = Relationship(back_populates="tenant")
    tasks: List["Task"] = Relationship(back_populates="tenant")
    
    __table_args__ = (
        Index("idx_tenant_status", "status"),
        Index("idx_tenant_type", "tenant_type"),
    )


class Task(TenantBase, SQLModel, table=True):
    """Military task/tasker with ETMS2 compliance and multi-tenant support"""
    __tablename__ = "task"
    
    # Primary identification
    id: Optional[str] = Field(default=None, primary_key=True, index=True)
    control_number: str = Field(index=True)  # Unique within tenant
    
    # Core task information
    title: str = Field(max_length=200)
    description: str = Field(sa_column=Column(Text))
    originator: str = Field(index=True)
    org_unit_id: str = Field(foreign_key="orgunit.id", index=True)
    
    # Classification and CUI
    classification: ClassificationLevel = Field(default=ClassificationLevel.UNCLASSIFIED)
    classification_portions: Optional[Dict[str, str]] = Field(default=None, sa_column=Column(JSON))
    cui_marked: bool = Field(default=False)
    cui_categories: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    
    # Timing and prioritization
    suspense_date: date = Field(index=True)
    internal_suspense_date: Optional[date] = None
    priority_score: float = Field(default=0.0, ge=0.0, le=1.0)
    expedite_flag: bool = Field(default=False)
    
    # Status and workflow
    status: TaskStatus = Field(default=TaskStatus.DRAFT, index=True)
    signature_required_level: Optional[str] = None
    
    # Records management
    record_series_id: Optional[str] = Field(index=True)
    disposition_date: Optional[date] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = Field(foreign_key="user.id")
    
    # JSON fields
    tags: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    task_metadata: Optional[Dict] = Field(default=None, sa_column=Column(JSON))
    
    # Relationships
    tenant: Optional["Tenant"] = Relationship(back_populates="tasks")
    assignments: List["Assignment"] = Relationship(back_populates="task")
    comments: List["Comment"] = Relationship(back_populates="task")
    attachments: List["Attachment"] = Relationship(back_populates="task")
    
    __table_args__ = (
        UniqueConstraint("tenant_id", "control_number", name="uq_tenant_control_number"),
        CheckConstraint("priority_score >= 0 AND priority_score <= 1"),
        Index("idx_task_tenant_status", "tenant_id", "status"),
        Index("idx_task_tenant_suspense", "tenant_id", "suspense_date"),
    )


class User(TenantBase, SQLModel, table=True):
    """User account with multi-tenant support for various organization types"""
    __tablename__ = "user"
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    upn: str = Field(index=True)  # Email/UPN - unique within tenant
    name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    # Organization
    org_unit_id: str = Field(foreign_key="orgunit.id", index=True)
    
    # Position info (flexible for different org types)
    title: Optional[str] = None  # Job title
    rank_grade: Optional[str] = None  # Military rank or corporate grade
    employee_id: Optional[str] = None  # Employee/service number
    manager_id: Optional[str] = Field(foreign_key="user.id", default=None)  # Direct manager
    
    # Contact
    phone: Optional[str] = None
    mobile_phone: Optional[str] = None
    office_symbol: Optional[str] = None  # Military office symbol or office number
    office_location: Optional[str] = None
    
    # Security
    clearance_level: Optional[ClassificationLevel] = None
    mfa_enabled: bool = Field(default=False)
    password_hash: Optional[str] = None  # For future auth implementation
    
    # Permissions
    roles: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    permissions: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    is_tenant_admin: bool = Field(default=False)
    is_system_admin: bool = Field(default=False)
    
    # Work settings
    working_hours: Optional[Dict] = Field(default=None, sa_column=Column(JSON))  # Start/end times
    timezone: Optional[str] = None
    notification_preferences: Dict = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Status
    is_active: bool = Field(default=True)
    is_available: bool = Field(default=True)
    out_of_office_until: Optional[date] = None
    out_of_office_message: Optional[str] = None
    
    # Skills and expertise (for task routing)
    skills: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    expertise_areas: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    profile_updated_at: Optional[datetime] = None
    
    # Relationships
    tenant: Optional["Tenant"] = Relationship(back_populates="users")
    org_unit: Optional["OrgUnit"] = Relationship(back_populates="users")
    
    __table_args__ = (
        UniqueConstraint("tenant_id", "upn", name="uq_tenant_upn"),
        Index("idx_user_tenant_active", "tenant_id", "is_active"),
    )


class OrgUnit(TenantBase, SQLModel, table=True):
    """Organizational unit - flexible for military, corporate, and small business structures"""
    __tablename__ = "orgunit"
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    name: str = Field(index=True)
    short_name: Optional[str] = None
    description: Optional[str] = None
    
    # Organization level/type (flexible)
    echelon: Optional[EchelonLevel] = None  # Optional, can be null for simple structures
    org_type: Optional[str] = None  # "department", "division", "team", "office", etc.
    
    # Hierarchy
    parent_id: Optional[str] = Field(foreign_key="orgunit.id", default=None)
    path: str = Field(index=True)  # Materialized path for efficient queries
    level: int = Field(default=0)  # Depth in hierarchy (0 = root)
    
    # Contact and location
    manager_id: Optional[str] = Field(foreign_key="user.id", default=None)
    location: Optional[str] = None
    address: Optional[Dict] = Field(default=None, sa_column=Column(JSON))
    timezone: str = Field(default="America/New_York")
    
    # Business info
    cost_center: Optional[str] = None  # For budgeting
    budget: Optional[float] = None
    currency: str = Field(default="USD")
    
    # External integrations
    uic: Optional[str] = None  # Military Unit Identification Code
    external_id: Optional[str] = None  # For integration with external systems (HRIS, ERP, etc.)
    external_system: Optional[str] = None  # Name of external system
    
    # Workflow and business rules
    approval_required: bool = Field(default=False)  # Tasks from this unit require approval
    auto_assign_to_manager: bool = Field(default=False)  # Auto-assign tasks to manager
    task_prefix: Optional[str] = None  # Prefix for task IDs from this unit
    
    # Configuration
    settings: Dict = Field(default_factory=dict, sa_column=Column(JSON))
    custom_fields: Dict = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Status
    active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    tenant: Optional["Tenant"] = Relationship(back_populates="org_units")
    users: List["User"] = Relationship(back_populates="org_unit")
    authorities: List["Authority"] = Relationship(back_populates="org_unit")
    parent: Optional["OrgUnit"] = Relationship(
        sa_relationship_kwargs={
            "remote_side": "OrgUnit.id",
            "foreign_keys": "[OrgUnit.parent_id]"
        }
    )
    
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_tenant_orgunit_name"),
        Index("idx_orgunit_tenant_path", "tenant_id", "path"),
        Index("idx_orgunit_tenant_active", "tenant_id", "active"),
    )


class Authority(TenantBase, SQLModel, table=True):
    """Approval authority with multi-tenant support"""
    __tablename__ = "authority"
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    title: str
    org_unit_id: str = Field(foreign_key="orgunit.id", index=True)
    
    # Authority level
    grade: str
    position_title: Optional[str] = None
    
    # Scope
    authority_scope: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    policy_areas: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    max_classification: ClassificationLevel = Field(default=ClassificationLevel.UNCLASSIFIED)
    
    # Delegation
    can_delegate: bool = Field(default=True)
    delegation_limit: Optional[str] = None
    precedence_order: int = Field(default=100)
    
    # Status
    current_incumbent: Optional[str] = Field(foreign_key="user.id", default=None)
    active: bool = Field(default=True)
    
    # Relationships
    org_unit: Optional["OrgUnit"] = Relationship(back_populates="authorities")
    incumbent: Optional["User"] = Relationship()
    
    __table_args__ = (
        Index("idx_authority_tenant_precedence", "tenant_id", "precedence_order"),
        Index("idx_authority_tenant_active", "tenant_id", "active"),
    )


class Assignment(TenantBase, SQLModel, table=True):
    """Task assignment with multi-tenant support"""
    __tablename__ = "assignment"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: str = Field(foreign_key="task.id", index=True)
    
    # Assignee
    assignee_type: str = Field(default="org")
    assignee_user_id: Optional[str] = Field(foreign_key="user.id", default=None)
    assignee_org_id: Optional[str] = Field(foreign_key="orgunit.id", default=None)
    
    # Role and state
    role: AssignmentRole
    state: AssignmentState = Field(default=AssignmentState.PENDING)
    
    # Timing
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    due_override_date: Optional[date] = None
    completed_at: Optional[datetime] = None
    
    # Response
    coordination_type: Optional[CoordinationType] = None
    rationale: Optional[str] = Field(default=None, sa_column=Column(Text))
    
    # Tracking
    assigned_by: str = Field(foreign_key="user.id")
    
    # Relationships
    task: Optional["Task"] = Relationship(back_populates="assignments")
    assignee_user: Optional["User"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Assignment.assignee_user_id]"}
    )
    assignee_org: Optional["OrgUnit"] = Relationship()
    
    __table_args__ = (
        CheckConstraint("(assignee_user_id IS NOT NULL) OR (assignee_org_id IS NOT NULL)"),
        Index("idx_assignment_tenant_task", "tenant_id", "task_id"),
        Index("idx_assignment_tenant_state", "tenant_id", "state"),
    )


class Comment(TenantBase, SQLModel, table=True):
    """Comments with multi-tenant support"""
    __tablename__ = "comment"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: str = Field(foreign_key="task.id", index=True)
    
    # Content
    author_user_id: str = Field(foreign_key="user.id")
    body: str = Field(sa_column=Column(Text))
    
    # Threading
    parent_comment_id: Optional[int] = Field(foreign_key="comment.id", default=None)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    edited_at: Optional[datetime] = None
    is_decision: bool = Field(default=False)
    
    # Classification
    classification: ClassificationLevel = Field(default=ClassificationLevel.UNCLASSIFIED)
    
    # Relationships
    task: Optional["Task"] = Relationship(back_populates="comments")
    author: Optional["User"] = Relationship()
    parent: Optional["Comment"] = Relationship(
        sa_relationship_kwargs={
            "remote_side": "Comment.id",
            "foreign_keys": "[Comment.parent_comment_id]"
        }
    )
    
    __table_args__ = (
        Index("idx_comment_tenant_task", "tenant_id", "task_id"),
    )


class Attachment(TenantBase, SQLModel, table=True):
    """Document attachments with multi-tenant support"""
    __tablename__ = "attachment"
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    task_id: str = Field(foreign_key="task.id", index=True)
    
    # File info
    filename: str
    mime_type: str
    size_bytes: int
    checksum: Optional[str] = None
    
    # Storage
    storage_ref: str  # Tenant-isolated storage path
    storage_type: str = Field(default="s3")
    
    # Security
    classification: ClassificationLevel = Field(default=ClassificationLevel.UNCLASSIFIED)
    cui_marked: bool = Field(default=False)
    
    # Metadata
    uploaded_by: str = Field(foreign_key="user.id")
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    task: Optional["Task"] = Relationship(back_populates="attachments")
    uploader: Optional["User"] = Relationship()
    
    __table_args__ = (
        Index("idx_attachment_tenant_task", "tenant_id", "task_id"),
    )


class AuditLog(SQLModel, table=True):
    """Immutable audit trail - system-wide, not tenant-specific"""
    __tablename__ = "audit_log"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Tenant context
    tenant_id: str = Field(index=True)
    
    # Target
    object_type: str = Field(index=True)
    object_id: str = Field(index=True)
    
    # Action
    actor_user_id: str = Field(index=True)
    action: str
    
    # Details
    details: Dict = Field(default_factory=dict, sa_column=Column(JSON))
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    # Timestamp
    ts: datetime = Field(default_factory=datetime.utcnow, index=True)
    
    # Relationships
    actor: Optional["User"] = Relationship()
    
    __table_args__ = (
        Index("idx_audit_tenant_ts", "tenant_id", "ts"),
        Index("idx_audit_tenant_object", "tenant_id", "object_type", "object_id"),
    )