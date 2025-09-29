# Copyright (c) 2025 Acarin Inc. All rights reserved.
# Proprietary and confidential.
"""Simplified SQLModel ORM models for MissionMind TasksMind."""
from __future__ import annotations

from datetime import datetime, date
from typing import List, Optional, Dict
from enum import Enum
from uuid import uuid4

from sqlalchemy import Column, JSON, Index, CheckConstraint, UniqueConstraint, Text
from sqlmodel import Field, SQLModel


# Enums
class TenantType(str, Enum):
    """Types of tenant organizations"""
    MILITARY = "military"
    GOVERNMENT = "government" 
    CONTRACTOR = "contractor"
    ALLIED = "allied"
    ENTERPRISE = "enterprise"
    SMALL_BUSINESS = "small_business"
    NONPROFIT = "nonprofit"
    STARTUP = "startup"
    CONSULTING = "consulting"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    LEGAL = "legal"
    FINANCIAL = "financial"
    TECHNOLOGY = "technology"


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


class EchelonLevel(str, Enum):
    """Organizational levels - flexible for different org types"""
    # Military levels
    HQDA = "HQDA"
    ACOM = "ACOM"
    ASCC = "ASCC"
    DRU = "DRU"
    CORPS = "CORPS"
    DIVISION = "DIVISION"
    BRIGADE = "BRIGADE"
    BATTALION = "BATTALION"
    COMPANY = "COMPANY"
    PLATOON = "PLATOON"
    SQUAD = "SQUAD"
    
    # Corporate levels
    CORPORATE = "CORPORATE"
    BUSINESS_UNIT = "BUSINESS_UNIT"
    REGION = "REGION"
    BRANCH = "BRANCH"
    DEPARTMENT = "DEPARTMENT"
    TEAM = "TEAM"
    
    # Generic levels
    LEVEL_1 = "LEVEL_1"
    LEVEL_2 = "LEVEL_2"
    LEVEL_3 = "LEVEL_3"
    LEVEL_4 = "LEVEL_4"
    LEVEL_5 = "LEVEL_5"


# Base model with tenant support
class TenantBase(SQLModel):
    """Base model with tenant_id for multi-tenancy"""
    tenant_id: str = Field(foreign_key="tenant.id", index=True)


# Primary Models (simplified without relationships)
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
    industry: Optional[str] = Field(default=None)
    country: str = Field(default="US")
    timezone: str = Field(default="America/New_York")
    company_size: Optional[str] = Field(default=None)
    
    # Configuration
    status: TenantStatus = Field(default=TenantStatus.PENDING)
    max_users: int = Field(default=50)
    max_storage_gb: int = Field(default=25)
    
    # Security
    allowed_classification_levels: List[ClassificationLevel] = Field(
        default_factory=lambda: [ClassificationLevel.UNCLASSIFIED],
        sa_column=Column(JSON)
    )
    require_mfa: bool = Field(default=False)
    
    # Customization
    settings: Dict = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    activated_at: Optional[datetime] = None
    
    __table_args__ = (
        Index("idx_tenant_status", "status"),
        Index("idx_tenant_type", "tenant_type"),
    )


class User(TenantBase, SQLModel, table=True):
    """User account with multi-tenant support"""
    __tablename__ = "user"
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    upn: str = Field(index=True)  # Email/UPN - unique within tenant
    name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    # Organization
    org_unit_id: Optional[str] = Field(foreign_key="orgunit.id", default=None, index=True)
    
    # Position info
    title: Optional[str] = None
    rank_grade: Optional[str] = None
    employee_id: Optional[str] = None
    
    # Contact
    phone: Optional[str] = None
    office_symbol: Optional[str] = None
    
    # Security
    clearance_level: Optional[ClassificationLevel] = None
    
    # Permissions
    roles: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    is_tenant_admin: bool = Field(default=False)
    is_system_admin: bool = Field(default=False)
    
    # Status
    is_active: bool = Field(default=True)
    is_available: bool = Field(default=True)
    out_of_office_until: Optional[date] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    
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
    echelon: Optional[EchelonLevel] = None
    org_type: Optional[str] = None
    
    # Hierarchy
    parent_id: Optional[str] = Field(foreign_key="orgunit.id", default=None)
    path: str = Field(index=True)  # Materialized path
    level: int = Field(default=0)
    
    # Contact and location
    location: Optional[str] = None
    timezone: str = Field(default="America/New_York")
    
    # Configuration
    settings: Dict = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Status
    active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_tenant_orgunit_name"),
        Index("idx_orgunit_tenant_path", "tenant_id", "path"),
        Index("idx_orgunit_tenant_active", "tenant_id", "active"),
    )