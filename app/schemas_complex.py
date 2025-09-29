# Copyright (c) 2025 Acarin Inc. All rights reserved.
# Proprietary and confidential.
"""Pydantic schemas for multi-tenant MissionMind APIs."""
from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional, Dict
from enum import Enum

from pydantic import BaseModel, Field, validator
from app.models import (
    TenantType, TenantStatus, ClassificationLevel, EchelonLevel
)


# Base schemas
class TenantContextBase(BaseModel):
    """Base schema that includes tenant context"""
    tenant_id: Optional[str] = Field(None, description="Tenant ID (set by system)")
    
    class Config:
        from_attributes = True


# Tenant schemas
class TenantBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=50, pattern="^[a-z0-9-]+$")
    display_name: str = Field(..., min_length=3, max_length=100)
    tenant_type: TenantType = TenantType.MILITARY
    organization_code: Optional[str] = None
    max_users: int = Field(100, ge=1, le=10000)
    max_storage_gb: int = Field(100, ge=1, le=100000)
    allowed_classification_levels: List[ClassificationLevel] = [ClassificationLevel.UNCLASSIFIED]
    require_mfa: bool = True
    branding: Optional[Dict] = None
    settings: Dict = Field(default_factory=dict)


class TenantCreate(TenantBase):
    """Schema for creating a new tenant"""
    pass


class TenantUpdate(BaseModel):
    """Schema for updating tenant"""
    display_name: Optional[str] = None
    status: Optional[TenantStatus] = None
    max_users: Optional[int] = None
    max_storage_gb: Optional[int] = None
    allowed_classification_levels: Optional[List[ClassificationLevel]] = None
    require_mfa: Optional[bool] = None
    branding: Optional[Dict] = None
    settings: Optional[Dict] = None


class TenantRead(TenantBase):
    """Schema for reading tenant data"""
    id: str
    status: TenantStatus
    created_at: datetime
    updated_at: datetime
    activated_at: Optional[datetime]
    
    # Statistics
    user_count: Optional[int] = None
    task_count: Optional[int] = None
    storage_used_gb: Optional[float] = None
    
    class Config:
        from_attributes = True


# User schemas
class UserBase(TenantContextBase):
    upn: str = Field(..., description="User Principal Name (email)")
    name: str
    org_unit_id: str
    rank_grade: Optional[str] = None
    phone: Optional[str] = None
    office_symbol: Optional[str] = None
    clearance_level: Optional[ClassificationLevel] = None
    roles: List[str] = Field(default_factory=list)
    is_tenant_admin: bool = False


class UserCreate(UserBase):
    """Schema for creating a user"""
    password: Optional[str] = Field(None, min_length=8)
    mfa_enabled: bool = False


class UserUpdate(BaseModel):
    """Schema for updating user"""
    name: Optional[str] = None
    org_unit_id: Optional[str] = None
    rank_grade: Optional[str] = None
    phone: Optional[str] = None
    office_symbol: Optional[str] = None
    clearance_level: Optional[ClassificationLevel] = None
    roles: Optional[List[str]] = None
    is_active: Optional[bool] = None
    is_available: Optional[bool] = None
    out_of_office_until: Optional[date] = None


class UserRead(UserBase):
    """Schema for reading user data"""
    id: str
    is_active: bool
    is_available: bool
    out_of_office_until: Optional[date]
    mfa_enabled: bool
    created_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True


# Organization Unit schemas
class OrgUnitBase(TenantContextBase):
    name: str
    short_name: Optional[str] = None
    echelon: Optional[EchelonLevel] = None
    parent_id: Optional[str] = None
    uic: Optional[str] = None
    external_id: Optional[str] = None
    timezone: str = "America/New_York"
    settings: Dict = Field(default_factory=dict)


class OrgUnitCreate(OrgUnitBase):
    """Schema for creating an org unit"""
    pass


class OrgUnitUpdate(BaseModel):
    """Schema for updating org unit"""
    name: Optional[str] = None
    short_name: Optional[str] = None
    echelon: Optional[EchelonLevel] = None
    parent_id: Optional[str] = None
    uic: Optional[str] = None
    external_id: Optional[str] = None
    timezone: Optional[str] = None
    settings: Optional[Dict] = None
    active: Optional[bool] = None


class OrgUnitRead(OrgUnitBase):
    """Schema for reading org unit data"""
    id: str
    path: str
    active: bool
    created_at: datetime
    user_count: Optional[int] = None
    
    class Config:
        from_attributes = True


# Authority schemas
class AuthorityBase(TenantContextBase):
    title: str
    org_unit_id: str
    grade: str
    position_title: Optional[str] = None
    authority_scope: List[str] = Field(default_factory=list)
    policy_areas: List[str] = Field(default_factory=list)
    max_classification: ClassificationLevel = ClassificationLevel.UNCLASSIFIED
    can_delegate: bool = True
    delegation_limit: Optional[str] = None
    precedence_order: int = 100


class AuthorityCreate(AuthorityBase):
    """Schema for creating authority"""
    pass


class AuthorityUpdate(BaseModel):
    """Schema for updating authority"""
    title: Optional[str] = None
    grade: Optional[str] = None
    position_title: Optional[str] = None
    authority_scope: Optional[List[str]] = None
    policy_areas: Optional[List[str]] = None
    max_classification: Optional[ClassificationLevel] = None
    can_delegate: Optional[bool] = None
    delegation_limit: Optional[str] = None
    precedence_order: Optional[int] = None
    current_incumbent: Optional[str] = None
    active: Optional[bool] = None


class AuthorityRead(AuthorityBase):
    """Schema for reading authority data"""
    id: str
    current_incumbent: Optional[str]
    active: bool
    
    class Config:
        from_attributes = True


class AuthoritySuggestion(BaseModel):
    """Authority recommendation"""
    authority_id: str
    title: str
    org_unit_id: str
    grade: str
    confidence: float
    rationale: str
    incumbent_available: bool = True


# Task schemas
class TaskBase(TenantContextBase):
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10)
    classification: ClassificationLevel
    suspense_date: date
    originator: str
    org_unit_id: str
    internal_suspense_date: Optional[date] = None
    expedite_flag: bool = False
    signature_required_level: Optional[str] = None
    record_series_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    task_metadata: Optional[Dict] = None


class TaskCreate(TaskBase):
    """Schema for creating a task"""
    control_number: Optional[str] = None
    
    @validator('suspense_date')
    def suspense_date_future(cls, v):
        if v < date.today():
            raise ValueError('Suspense date must be in the future')
        return v


class TaskUpdate(BaseModel):
    """Schema for updating task"""
    title: Optional[str] = None
    description: Optional[str] = None
    classification: Optional[ClassificationLevel] = None
    suspense_date: Optional[date] = None
    internal_suspense_date: Optional[date] = None
    originator: Optional[str] = None
    org_unit_id: Optional[str] = None
    status: Optional[TaskStatus] = None
    expedite_flag: Optional[bool] = None
    signature_required_level: Optional[str] = None
    record_series_id: Optional[str] = None
    tags: Optional[List[str]] = None
    task_metadata: Optional[Dict] = None


class TaskRead(TaskBase):
    """Schema for reading task data"""
    id: str
    control_number: str
    priority_score: float
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    assignments: List["AssignmentRead"] = Field(default_factory=list)
    comment_count: Optional[int] = 0
    attachment_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


# Assignment schemas
class AssignmentBase(TenantContextBase):
    assignee_type: str = Field(default="org", pattern="^(org|user)$")
    assignee_user_id: Optional[str] = None
    assignee_org_id: Optional[str] = None
    role: AssignmentRole
    due_override_date: Optional[date] = None
    
    @validator('assignee_user_id', 'assignee_org_id')
    def check_assignee(cls, v, values):
        if 'assignee_type' in values:
            if values['assignee_type'] == 'user' and not values.get('assignee_user_id'):
                raise ValueError('assignee_user_id required when assignee_type is user')
            if values['assignee_type'] == 'org' and not values.get('assignee_org_id'):
                raise ValueError('assignee_org_id required when assignee_type is org')
        return v


class AssignmentCreate(AssignmentBase):
    """Schema for creating assignment"""
    pass


class AssignmentUpdate(BaseModel):
    """Schema for updating assignment"""
    state: Optional[AssignmentState] = None
    due_override_date: Optional[date] = None
    coordination_type: Optional[CoordinationType] = None
    rationale: Optional[str] = None


class AssignmentRead(AssignmentBase):
    """Schema for reading assignment"""
    id: int
    task_id: str
    state: AssignmentState
    assigned_at: datetime
    assigned_by: str
    completed_at: Optional[datetime]
    coordination_type: Optional[CoordinationType]
    rationale: Optional[str]
    
    class Config:
        from_attributes = True


# Comment schemas
class CommentBase(TenantContextBase):
    body: str = Field(..., min_length=1)
    parent_comment_id: Optional[int] = None
    is_decision: bool = False
    classification: ClassificationLevel = ClassificationLevel.UNCLASSIFIED


class CommentCreate(CommentBase):
    """Schema for creating comment"""
    pass


class CommentUpdate(BaseModel):
    """Schema for updating comment"""
    body: Optional[str] = None
    is_decision: Optional[bool] = None


class CommentRead(CommentBase):
    """Schema for reading comment"""
    id: int
    task_id: str
    author_user_id: str
    author_name: Optional[str] = None
    created_at: datetime
    edited_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# Additional schemas
class TaskSummary(BaseModel):
    """AI-generated task summary"""
    task_id: str
    summary: str
    risk_level: RiskLevel
    key_points: List[str]
    next_actions: List[str]


class RiskInsight(BaseModel):
    """Risk analysis for a task"""
    task_id: str
    risk_level: RiskLevel
    late_probability: float = Field(..., ge=0.0, le=1.0)
    drivers: List[str]
    recommended_actions: List[str]
    historical_context: Optional[Dict] = None


class QualityIssue(BaseModel):
    """Quality check issue"""
    code: str
    severity: str = Field(..., pattern="^(low|medium|high|critical)$")
    message: str
    field: Optional[str] = None


class QualityCheckResult(BaseModel):
    """Quality check results"""
    task_id: str
    issues: List[QualityIssue]
    passed: bool
    score: float = Field(..., ge=0.0, le=1.0)


class TaskListFilters(BaseModel):
    """Filters for task listing"""
    status: Optional[TaskStatus] = None
    due_before: Optional[date] = None
    due_after: Optional[date] = None
    org_unit_id: Optional[str] = None
    assigned_to_user: Optional[str] = None
    assigned_to_org: Optional[str] = None
    classification: Optional[ClassificationLevel] = None
    tags: Optional[List[str]] = None
    search: Optional[str] = None
    
    
# Update forward references
TaskRead.update_forward_refs()
AssignmentRead.update_forward_refs()