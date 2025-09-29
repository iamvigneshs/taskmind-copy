# Copyright (c) 2025 Acarin Inc. All rights reserved.
# Proprietary and confidential.
"""Simplified Pydantic schemas for multi-tenant MissionMind APIs."""
from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional, Dict

from pydantic import BaseModel, Field
from app.models import TenantType, TenantStatus, ClassificationLevel, EchelonLevel


# Base schemas
class TenantContextBase(BaseModel):
    """Base schema that includes tenant context"""
    tenant_id: Optional[str] = Field(None, description="Tenant ID (set by system)")

    class Config:
        from_attributes = True


# Tenant schemas
class TenantBase(BaseModel):
    """Base tenant schema"""
    name: str = Field(..., min_length=2, max_length=100)
    display_name: str = Field(..., min_length=2, max_length=200)
    tenant_type: TenantType = TenantType.SMALL_BUSINESS
    organization_code: Optional[str] = Field(None, max_length=50)
    
    # Business details
    industry: Optional[str] = Field(None, max_length=100)
    country: str = Field(default="US", max_length=2)
    timezone: str = Field(default="America/New_York", max_length=50)
    company_size: Optional[str] = Field(None, max_length=20)
    
    # Configuration
    max_users: int = Field(default=50, ge=1, le=10000)
    max_storage_gb: int = Field(default=25, ge=1, le=1000)
    
    # Security
    allowed_classification_levels: List[ClassificationLevel] = Field(
        default_factory=lambda: [ClassificationLevel.UNCLASSIFIED]
    )
    require_mfa: bool = Field(default=False)
    
    # Settings
    settings: Dict = Field(default_factory=dict)


class TenantCreate(TenantBase):
    """Schema for creating tenant"""
    pass


class TenantUpdate(BaseModel):
    """Schema for updating tenant"""
    display_name: Optional[str] = Field(None, min_length=2, max_length=200)
    industry: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=2)
    timezone: Optional[str] = Field(None, max_length=50)
    company_size: Optional[str] = Field(None, max_length=20)
    max_users: Optional[int] = Field(None, ge=1, le=10000)
    max_storage_gb: Optional[int] = Field(None, ge=1, le=1000)
    allowed_classification_levels: Optional[List[ClassificationLevel]] = None
    require_mfa: Optional[bool] = None
    settings: Optional[Dict] = None

    class Config:
        from_attributes = True


class TenantRead(TenantBase):
    """Schema for reading tenant data"""
    id: str
    status: TenantStatus
    created_at: datetime
    updated_at: datetime
    activated_at: Optional[datetime] = None
    
    # Statistics (populated by API)
    user_count: Optional[int] = 0
    task_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


# User schemas
class UserBase(TenantContextBase):
    """Base user schema"""
    upn: str = Field(..., min_length=3, max_length=200)  # Email/UPN
    name: str = Field(..., min_length=2, max_length=200)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    
    # Organization
    org_unit_id: Optional[str] = None
    
    # Position
    title: Optional[str] = Field(None, max_length=100)
    rank_grade: Optional[str] = Field(None, max_length=50)
    employee_id: Optional[str] = Field(None, max_length=50)
    
    # Contact
    phone: Optional[str] = Field(None, max_length=20)
    office_symbol: Optional[str] = Field(None, max_length=50)
    
    # Security
    clearance_level: Optional[ClassificationLevel] = None
    
    # Permissions
    roles: List[str] = Field(default_factory=list)
    is_tenant_admin: bool = Field(default=False)
    is_system_admin: bool = Field(default=False)
    
    # Status
    is_active: bool = Field(default=True)
    is_available: bool = Field(default=True)
    out_of_office_until: Optional[date] = None


class UserCreate(UserBase):
    """Schema for creating user"""
    password: Optional[str] = Field(None, min_length=8)  # For future use


class UserUpdate(BaseModel):
    """Schema for updating user"""
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    org_unit_id: Optional[str] = None
    title: Optional[str] = Field(None, max_length=100)
    rank_grade: Optional[str] = Field(None, max_length=50)
    employee_id: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    office_symbol: Optional[str] = Field(None, max_length=50)
    clearance_level: Optional[ClassificationLevel] = None
    roles: Optional[List[str]] = None
    is_tenant_admin: Optional[bool] = None
    is_active: Optional[bool] = None
    is_available: Optional[bool] = None
    out_of_office_until: Optional[date] = None

    class Config:
        from_attributes = True


class UserRead(UserBase):
    """Schema for reading user data"""
    id: str
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Organization Unit schemas
class OrgUnitBase(TenantContextBase):
    """Base org unit schema"""
    name: str = Field(..., min_length=2, max_length=200)
    short_name: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    
    # Organization level/type
    echelon: Optional[EchelonLevel] = None
    org_type: Optional[str] = Field(None, max_length=50)
    
    # Hierarchy
    parent_id: Optional[str] = None
    
    # Contact and location
    location: Optional[str] = Field(None, max_length=200)
    timezone: str = Field(default="America/New_York", max_length=50)
    
    # Configuration
    settings: Dict = Field(default_factory=dict)
    
    # Status
    active: bool = Field(default=True)


class OrgUnitCreate(OrgUnitBase):
    """Schema for creating org unit"""
    pass


class OrgUnitUpdate(BaseModel):
    """Schema for updating org unit"""
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    short_name: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    echelon: Optional[EchelonLevel] = None
    org_type: Optional[str] = Field(None, max_length=50)
    parent_id: Optional[str] = None
    location: Optional[str] = Field(None, max_length=200)
    timezone: Optional[str] = Field(None, max_length=50)
    settings: Optional[Dict] = None
    active: Optional[bool] = None

    class Config:
        from_attributes = True


class OrgUnitRead(OrgUnitBase):
    """Schema for reading org unit data"""
    id: str
    path: str
    level: int
    created_at: datetime
    updated_at: datetime
    
    # Statistics (populated by API)
    user_count: Optional[int] = 0
    
    class Config:
        from_attributes = True