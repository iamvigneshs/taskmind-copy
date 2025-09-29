# Copyright (c) 2025 Acarin Inc. All rights reserved.
# Proprietary and confidential.
"""Configurable organization templates and approval workflows."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from uuid import uuid4

from sqlalchemy import Column, JSON, String, Index, Text, Boolean, Integer
from sqlmodel import Field, Relationship, SQLModel

from app.models import TenantBase


class TemplateType(str, Enum):
    """Types of organizational templates"""
    MILITARY = "military"
    CORPORATE = "corporate"
    GOVERNMENT = "government"
    SMALL_BUSINESS = "small_business"
    NONPROFIT = "nonprofit"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"


class ApprovalTrigger(str, Enum):
    """When approval is required"""
    ALWAYS = "always"
    AMOUNT_THRESHOLD = "amount_threshold" 
    CLASSIFICATION_LEVEL = "classification_level"
    TASK_TYPE = "task_type"
    ORIGINATOR = "originator"
    TIMELINE = "timeline"
    CUSTOM_RULE = "custom_rule"


class OrgLevelTemplate(TenantBase, SQLModel, table=True):
    """Template for organizational levels and hierarchies"""
    __tablename__ = "org_level_template"
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    name: str = Field(index=True)  # e.g., "US Army Structure", "Corporate Hierarchy"
    template_type: TemplateType
    description: Optional[str] = None
    
    # Template definition
    levels: List[Dict[str, Any]] = Field(sa_column=Column(JSON))
    # Example: [
    #   {"level": 0, "name": "HQDA", "display_name": "Headquarters Department of Army", "abbrev": "HQDA"},
    #   {"level": 1, "name": "ACOM", "display_name": "Army Command", "abbrev": "ACOM"},
    #   {"level": 2, "name": "CORPS", "display_name": "Corps", "abbrev": "CORPS"}
    # ]
    
    # Business rules
    max_levels: int = Field(default=10)
    allows_matrix_structure: bool = Field(default=False)  # Can units report to multiple parents
    requires_unique_names: bool = Field(default=True)
    
    # Approval flow settings
    default_approval_flow: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Metadata
    is_active: bool = Field(default=True)
    is_system_template: bool = Field(default=False)  # System templates can't be deleted
    created_by: Optional[str] = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    approval_templates: List["ApprovalTemplate"] = Relationship(back_populates="org_template")
    
    __table_args__ = (
        Index("idx_org_template_tenant_type", "tenant_id", "template_type"),
        Index("idx_org_template_active", "is_active"),
    )


class ApprovalTemplate(TenantBase, SQLModel, table=True):
    """Configurable approval and authorization templates"""
    __tablename__ = "approval_template"
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    name: str = Field(index=True)  # e.g., "Army Task Approval", "Corporate Budget Approval"
    org_template_id: str = Field(foreign_key="org_level_template.id", index=True)
    
    # Approval rules
    approval_rules: List[Dict[str, Any]] = Field(sa_column=Column(JSON))
    # Example: [
    #   {
    #     "trigger": "classification_level", 
    #     "condition": "SECRET", 
    #     "required_level": "O6",
    #     "required_clearance": "SECRET",
    #     "escalation_days": 3
    #   },
    #   {
    #     "trigger": "amount_threshold",
    #     "condition": "> 50000",
    #     "required_level": "SES",
    #     "approval_chain": ["immediate_supervisor", "division_chief", "director"]
    #   }
    # ]
    
    # Authority matrix
    authority_matrix: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    # Maps roles/levels to what they can approve
    # Example: {
    #   "O6": {"max_classification": "SECRET", "max_amount": 100000, "can_delegate": true},
    #   "SES": {"max_classification": "TS", "max_amount": 1000000, "can_delegate": true}
    # }
    
    # Escalation rules
    escalation_rules: List[Dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    # Example: [
    #   {"days_overdue": 1, "action": "reminder", "to": "approver"},
    #   {"days_overdue": 3, "action": "escalate", "to": "supervisor"},
    #   {"days_overdue": 7, "action": "auto_approve", "conditions": ["low_risk"]}
    # ]
    
    # Delegation rules
    delegation_rules: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Workflow settings
    requires_sequential_approval: bool = Field(default=True)
    allows_parallel_approval: bool = Field(default=False)
    auto_assign_based_on_workload: bool = Field(default=False)
    
    # Metadata
    is_active: bool = Field(default=True)
    created_by: Optional[str] = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    org_template: Optional["OrgLevelTemplate"] = Relationship(back_populates="approval_templates")
    
    __table_args__ = (
        Index("idx_approval_template_tenant_active", "tenant_id", "is_active"),
    )


class AuthorityPosition(TenantBase, SQLModel, table=True):
    """Configurable authority positions within org templates"""
    __tablename__ = "authority_position"
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    org_template_id: str = Field(foreign_key="org_level_template.id", index=True)
    
    # Position definition
    position_name: str  # e.g., "Division Commander", "Branch Chief", "CEO"
    position_code: str  # e.g., "DIV_CMD", "BRANCH_CHIEF", "CEO"
    level: int  # Organizational level (0 = highest)
    
    # Authority scope
    grade_equivalent: Optional[str] = None  # Military: "O6", Corporate: "VP", "Director"
    authority_scope: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    max_classification_level: Optional[str] = None
    max_budget_authority: Optional[float] = None
    currency: str = Field(default="USD")
    
    # Approval powers
    can_approve_tasks: bool = Field(default=True)
    can_delegate_authority: bool = Field(default=False)
    can_create_positions: bool = Field(default=False)
    requires_supervisor_approval: bool = Field(default=False)
    
    # Succession planning
    succession_positions: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    acting_position_duration_days: Optional[int] = None
    
    # Configuration
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_authority_position_template_level", "org_template_id", "level"),
    )


# System templates - loaded as defaults
ARMY_ORG_TEMPLATE = {
    "name": "US Army Organizational Structure",
    "template_type": "military",
    "description": "Standard US Army hierarchical structure per AR 10-87",
    "levels": [
        {"level": 0, "name": "HQDA", "display_name": "Headquarters, Department of the Army", "abbrev": "HQDA", "typical_size": "500000+"},
        {"level": 1, "name": "ACOM", "display_name": "Army Command", "abbrev": "ACOM", "typical_size": "50000-200000"},
        {"level": 2, "name": "ASCC", "display_name": "Army Service Component Command", "abbrev": "ASCC", "typical_size": "20000-100000"},
        {"level": 3, "name": "CORPS", "display_name": "Corps", "abbrev": "CORPS", "typical_size": "20000-45000"},
        {"level": 4, "name": "DIVISION", "display_name": "Division", "abbrev": "DIV", "typical_size": "10000-18000"},
        {"level": 5, "name": "BRIGADE", "display_name": "Brigade", "abbrev": "BDE", "typical_size": "3000-5000"},
        {"level": 6, "name": "BATTALION", "display_name": "Battalion", "abbrev": "BN", "typical_size": "400-1000"},
        {"level": 7, "name": "COMPANY", "display_name": "Company", "abbrev": "CO", "typical_size": "100-200"},
        {"level": 8, "name": "PLATOON", "display_name": "Platoon", "abbrev": "PLT", "typical_size": "30-40"},
        {"level": 9, "name": "SQUAD", "display_name": "Squad", "abbrev": "SQD", "typical_size": "8-12"}
    ],
    "max_levels": 10,
    "allows_matrix_structure": False,
    "requires_unique_names": True
}

ARMY_APPROVAL_TEMPLATE = {
    "name": "US Army Task Approval Workflow",
    "approval_rules": [
        {
            "trigger": "classification_level",
            "condition": "SECRET",
            "required_level": "O6",
            "required_clearance": "SECRET",
            "escalation_days": 2,
            "description": "Secret tasks require O6+ approval"
        },
        {
            "trigger": "classification_level", 
            "condition": "TOP_SECRET",
            "required_level": "GO",
            "required_clearance": "TS",
            "escalation_days": 1,
            "description": "Top Secret tasks require General Officer approval"
        },
        {
            "trigger": "task_type",
            "condition": "deployment",
            "required_level": "O6",
            "approval_chain": ["bn_cmd", "bde_cmd", "div_cmd"],
            "description": "Deployment tasks require command approval chain"
        },
        {
            "trigger": "timeline",
            "condition": "< 24 hours",
            "required_level": "O5",
            "allows_verbal_approval": True,
            "requires_followup_written": True,
            "description": "Urgent tasks can have verbal approval"
        }
    ],
    "authority_matrix": {
        "E1-E4": {"max_classification": "U", "can_delegate": False, "approval_authority": "none"},
        "E5-E6": {"max_classification": "U", "can_delegate": False, "approval_authority": "squad_level"},
        "E7-E9": {"max_classification": "C", "can_delegate": True, "approval_authority": "company_level"},
        "O1-O3": {"max_classification": "C", "can_delegate": True, "approval_authority": "company_level"},
        "O4-O5": {"max_classification": "S", "can_delegate": True, "approval_authority": "battalion_level"},
        "O6": {"max_classification": "S", "can_delegate": True, "approval_authority": "brigade_level"},
        "O7-O10": {"max_classification": "TS", "can_delegate": True, "approval_authority": "division_plus"},
        "GS13-GS14": {"max_classification": "S", "can_delegate": True, "approval_authority": "branch_level"},
        "GS15": {"max_classification": "TS", "can_delegate": True, "approval_authority": "division_level"},
        "SES": {"max_classification": "TS", "can_delegate": True, "approval_authority": "command_level"}
    },
    "escalation_rules": [
        {"days_overdue": 1, "action": "reminder", "to": "approver"},
        {"days_overdue": 2, "action": "notify_supervisor", "to": "approver_supervisor"},
        {"days_overdue": 3, "action": "escalate", "to": "next_level"},
        {"days_overdue": 7, "action": "command_attention", "to": "command_group"}
    ]
}

CORPORATE_ORG_TEMPLATE = {
    "name": "Standard Corporate Hierarchy",
    "template_type": "corporate",
    "description": "Typical corporate organizational structure",
    "levels": [
        {"level": 0, "name": "CORPORATE", "display_name": "Corporate Headquarters", "abbrev": "CORP", "typical_size": "10000+"},
        {"level": 1, "name": "BUSINESS_UNIT", "display_name": "Business Unit", "abbrev": "BU", "typical_size": "1000-5000"},
        {"level": 2, "name": "DIVISION", "display_name": "Division", "abbrev": "DIV", "typical_size": "500-2000"},
        {"level": 3, "name": "REGION", "display_name": "Regional Office", "abbrev": "REGION", "typical_size": "100-500"},
        {"level": 4, "name": "DEPARTMENT", "display_name": "Department", "abbrev": "DEPT", "typical_size": "20-100"},
        {"level": 5, "name": "TEAM", "display_name": "Team", "abbrev": "TEAM", "typical_size": "5-20"}
    ],
    "max_levels": 6,
    "allows_matrix_structure": True,
    "requires_unique_names": False
}

SMALL_BUSINESS_TEMPLATE = {
    "name": "Small Business Structure", 
    "template_type": "small_business",
    "description": "Flexible structure for small businesses (1-100 employees)",
    "levels": [
        {"level": 0, "name": "COMPANY", "display_name": "Company", "abbrev": "CO", "typical_size": "1-100"},
        {"level": 1, "name": "DEPARTMENT", "display_name": "Department", "abbrev": "DEPT", "typical_size": "5-20"},
        {"level": 2, "name": "TEAM", "display_name": "Team", "abbrev": "TEAM", "typical_size": "2-8"}
    ],
    "max_levels": 3,
    "allows_matrix_structure": True,
    "requires_unique_names": False
}