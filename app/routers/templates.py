# Copyright (c) 2025 Acarin Inc. All rights reserved.
# Proprietary and confidential.
"""Organization and approval template management API."""
from __future__ import annotations

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, and_

from app.database import get_session
from app.models_templates import (
    OrgLevelTemplate, ApprovalTemplate, AuthorityPosition, TemplateType,
    ARMY_ORG_TEMPLATE, ARMY_APPROVAL_TEMPLATE, CORPORATE_ORG_TEMPLATE, SMALL_BUSINESS_TEMPLATE
)
from app.dependencies import get_current_user, get_current_tenant, require_tenant_admin

router = APIRouter(prefix="/templates", tags=["templates"])


# Org Level Template endpoints
@router.get("/org-levels", response_model=List[Dict[str, Any]])
def list_org_templates(
    template_type: Optional[TemplateType] = Query(None),
    include_system: bool = Query(True, description="Include system templates"),
    session: Session = Depends(get_session),
    tenant_id: str = Depends(get_current_tenant)
) -> List[Dict[str, Any]]:
    """List available organizational level templates."""
    statement = select(OrgLevelTemplate).where(
        and_(
            OrgLevelTemplate.tenant_id == tenant_id,
            OrgLevelTemplate.is_active == True
        )
    )
    
    if template_type:
        statement = statement.where(OrgLevelTemplate.template_type == template_type)
    
    if not include_system:
        statement = statement.where(OrgLevelTemplate.is_system_template == False)
    
    templates = session.exec(statement).all()
    
    return [
        {
            "id": t.id,
            "name": t.name,
            "template_type": t.template_type,
            "description": t.description,
            "levels": t.levels,
            "max_levels": t.max_levels,
            "allows_matrix_structure": t.allows_matrix_structure,
            "is_system_template": t.is_system_template,
            "created_at": t.created_at
        }
        for t in templates
    ]


@router.post("/org-levels", response_model=Dict[str, Any])
def create_org_template(
    name: str,
    template_type: TemplateType,
    levels: List[Dict[str, Any]],
    description: Optional[str] = None,
    max_levels: int = 10,
    allows_matrix_structure: bool = False,
    session: Session = Depends(get_session),
    current_user = Depends(require_tenant_admin),
    tenant_id: str = Depends(get_current_tenant)
) -> Dict[str, Any]:
    """Create a custom organizational level template."""
    # Validate levels structure
    required_fields = ["level", "name", "display_name"]
    for level_def in levels:
        if not all(field in level_def for field in required_fields):
            raise HTTPException(
                status_code=400,
                detail=f"Each level must have: {required_fields}"
            )
    
    # Check for duplicate name
    existing = session.exec(
        select(OrgLevelTemplate).where(
            and_(
                OrgLevelTemplate.tenant_id == tenant_id,
                OrgLevelTemplate.name == name
            )
        )
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail=f"Template '{name}' already exists")
    
    template = OrgLevelTemplate(
        tenant_id=tenant_id,
        name=name,
        template_type=template_type,
        description=description,
        levels=levels,
        max_levels=max_levels,
        allows_matrix_structure=allows_matrix_structure,
        created_by=current_user.id
    )
    
    session.add(template)
    session.commit()
    session.refresh(template)
    
    return {
        "id": template.id,
        "name": template.name,
        "template_type": template.template_type,
        "levels": template.levels,
        "message": "Org level template created successfully"
    }


@router.get("/org-levels/{template_id}")
def get_org_template(
    template_id: str,
    session: Session = Depends(get_session),
    tenant_id: str = Depends(get_current_tenant)
) -> Dict[str, Any]:
    """Get detailed org level template."""
    template = session.get(OrgLevelTemplate, template_id)
    if not template or template.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Include associated approval templates
    approval_templates = session.exec(
        select(ApprovalTemplate).where(ApprovalTemplate.org_template_id == template_id)
    ).all()
    
    return {
        "id": template.id,
        "name": template.name,
        "template_type": template.template_type,
        "description": template.description,
        "levels": template.levels,
        "max_levels": template.max_levels,
        "allows_matrix_structure": template.allows_matrix_structure,
        "default_approval_flow": template.default_approval_flow,
        "approval_templates": [
            {"id": at.id, "name": at.name, "is_active": at.is_active}
            for at in approval_templates
        ],
        "is_system_template": template.is_system_template,
        "created_at": template.created_at
    }


# Approval Template endpoints
@router.get("/approvals", response_model=List[Dict[str, Any]])
def list_approval_templates(
    org_template_id: Optional[str] = Query(None),
    session: Session = Depends(get_session),
    tenant_id: str = Depends(get_current_tenant)
) -> List[Dict[str, Any]]:
    """List approval templates."""
    statement = select(ApprovalTemplate).where(
        and_(
            ApprovalTemplate.tenant_id == tenant_id,
            ApprovalTemplate.is_active == True
        )
    )
    
    if org_template_id:
        statement = statement.where(ApprovalTemplate.org_template_id == org_template_id)
    
    templates = session.exec(statement).all()
    
    return [
        {
            "id": t.id,
            "name": t.name,
            "org_template_id": t.org_template_id,
            "approval_rules": t.approval_rules,
            "authority_matrix": t.authority_matrix,
            "escalation_rules": t.escalation_rules,
            "requires_sequential_approval": t.requires_sequential_approval,
            "created_at": t.created_at
        }
        for t in templates
    ]


@router.post("/approvals", response_model=Dict[str, Any])
def create_approval_template(
    name: str,
    org_template_id: str,
    approval_rules: List[Dict[str, Any]],
    authority_matrix: Dict[str, Any],
    escalation_rules: Optional[List[Dict[str, Any]]] = None,
    requires_sequential_approval: bool = True,
    session: Session = Depends(get_session),
    current_user = Depends(require_tenant_admin),
    tenant_id: str = Depends(get_current_tenant)
) -> Dict[str, Any]:
    """Create approval template."""
    # Verify org template exists and belongs to tenant
    org_template = session.get(OrgLevelTemplate, org_template_id)
    if not org_template or org_template.tenant_id != tenant_id:
        raise HTTPException(status_code=400, detail="Invalid org template")
    
    template = ApprovalTemplate(
        tenant_id=tenant_id,
        name=name,
        org_template_id=org_template_id,
        approval_rules=approval_rules,
        authority_matrix=authority_matrix,
        escalation_rules=escalation_rules or [],
        requires_sequential_approval=requires_sequential_approval,
        created_by=current_user.id
    )
    
    session.add(template)
    session.commit()
    session.refresh(template)
    
    return {
        "id": template.id,
        "name": template.name,
        "message": "Approval template created successfully"
    }


# System template initialization
@router.post("/init-system-templates", response_model=Dict[str, Any])
def initialize_system_templates(
    template_types: Optional[List[TemplateType]] = Query(None),
    session: Session = Depends(get_session),
    current_user = Depends(require_tenant_admin),
    tenant_id: str = Depends(get_current_tenant)
) -> Dict[str, Any]:
    """Initialize system templates for tenant."""
    created = []
    
    if not template_types:
        template_types = [TemplateType.MILITARY, TemplateType.CORPORATE, TemplateType.SMALL_BUSINESS]
    
    for template_type in template_types:
        if template_type == TemplateType.MILITARY:
            # Create Army org template
            existing = session.exec(
                select(OrgLevelTemplate).where(
                    and_(
                        OrgLevelTemplate.tenant_id == tenant_id,
                        OrgLevelTemplate.name == ARMY_ORG_TEMPLATE["name"]
                    )
                )
            ).first()
            
            if not existing:
                army_template = OrgLevelTemplate(
                    tenant_id=tenant_id,
                    is_system_template=True,
                    created_by=current_user.id,
                    **ARMY_ORG_TEMPLATE
                )
                session.add(army_template)
                session.flush()  # Get the ID
                
                # Create Army approval template
                army_approval = ApprovalTemplate(
                    tenant_id=tenant_id,
                    org_template_id=army_template.id,
                    created_by=current_user.id,
                    **ARMY_APPROVAL_TEMPLATE
                )
                session.add(army_approval)
                created.append("Army templates")
        
        elif template_type == TemplateType.CORPORATE:
            existing = session.exec(
                select(OrgLevelTemplate).where(
                    and_(
                        OrgLevelTemplate.tenant_id == tenant_id,
                        OrgLevelTemplate.name == CORPORATE_ORG_TEMPLATE["name"]
                    )
                )
            ).first()
            
            if not existing:
                corp_template = OrgLevelTemplate(
                    tenant_id=tenant_id,
                    is_system_template=True,
                    created_by=current_user.id,
                    **CORPORATE_ORG_TEMPLATE
                )
                session.add(corp_template)
                created.append("Corporate template")
        
        elif template_type == TemplateType.SMALL_BUSINESS:
            existing = session.exec(
                select(OrgLevelTemplate).where(
                    and_(
                        OrgLevelTemplate.tenant_id == tenant_id,
                        OrgLevelTemplate.name == SMALL_BUSINESS_TEMPLATE["name"]
                    )
                )
            ).first()
            
            if not existing:
                small_biz_template = OrgLevelTemplate(
                    tenant_id=tenant_id,
                    is_system_template=True,
                    created_by=current_user.id,
                    **SMALL_BUSINESS_TEMPLATE
                )
                session.add(small_biz_template)
                created.append("Small business template")
    
    session.commit()
    
    return {
        "message": "System templates initialized",
        "created": created,
        "tenant_id": tenant_id
    }


@router.get("/preview/{template_type}")
def preview_system_template(
    template_type: TemplateType
) -> Dict[str, Any]:
    """Preview system template structure before creating."""
    if template_type == TemplateType.MILITARY:
        return {
            "org_template": ARMY_ORG_TEMPLATE,
            "approval_template": ARMY_APPROVAL_TEMPLATE
        }
    elif template_type == TemplateType.CORPORATE:
        return {"org_template": CORPORATE_ORG_TEMPLATE}
    elif template_type == TemplateType.SMALL_BUSINESS:
        return {"org_template": SMALL_BUSINESS_TEMPLATE}
    else:
        raise HTTPException(status_code=400, detail=f"No system template for {template_type}")


@router.get("/authority-levels/{template_id}")
def get_authority_levels(
    template_id: str,
    session: Session = Depends(get_session),
    tenant_id: str = Depends(get_current_tenant)
) -> List[Dict[str, Any]]:
    """Get authority levels for an org template."""
    template = session.get(OrgLevelTemplate, template_id)
    if not template or template.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Template not found")
    
    positions = session.exec(
        select(AuthorityPosition).where(
            AuthorityPosition.org_template_id == template_id
        ).order_by(AuthorityPosition.level)
    ).all()
    
    return [
        {
            "id": pos.id,
            "position_name": pos.position_name,
            "position_code": pos.position_code,
            "level": pos.level,
            "grade_equivalent": pos.grade_equivalent,
            "authority_scope": pos.authority_scope,
            "max_classification_level": pos.max_classification_level,
            "max_budget_authority": pos.max_budget_authority,
            "can_approve_tasks": pos.can_approve_tasks,
            "can_delegate_authority": pos.can_delegate_authority
        }
        for pos in positions
    ]