# Copyright (c) 2025 Acarin Inc. All rights reserved.
# Proprietary and confidential.
"""Organization unit management API routes."""
from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, and_

from app.database import get_session
from app.models import OrgUnit, User
from app.schemas import OrgUnitCreate, OrgUnitRead, OrgUnitUpdate
from app.dependencies import get_current_user, get_current_tenant, TenantContext

router = APIRouter(prefix="/orgunits", tags=["orgunits"])


def _build_path(parent_path: Optional[str], name: str) -> str:
    """Build materialized path for org unit."""
    if parent_path:
        return f"{parent_path}/{name.lower().replace(' ', '-')}"
    return f"/{name.lower().replace(' ', '-')}"


@router.post("/", response_model=OrgUnitRead)
def create_org_unit(
    org_unit_in: OrgUnitCreate,
    session: Session = Depends(get_session),
    ctx: TenantContext = Depends(TenantContext)
) -> OrgUnitRead:
    """Create a new organization unit."""
    # Only tenant admins can create org units
    if not ctx.current_user.is_tenant_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Check if name already exists in tenant
    existing = session.exec(
        select(OrgUnit).where(
            and_(
                OrgUnit.tenant_id == ctx.tenant_id,
                OrgUnit.name == org_unit_in.name
            )
        )
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Org unit '{org_unit_in.name}' already exists")
    
    # Verify parent if specified
    parent_path = None
    if org_unit_in.parent_id:
        parent = session.get(OrgUnit, org_unit_in.parent_id)
        ctx.check_access(parent)
        parent_path = parent.path
    
    # Create org unit
    org_unit_data = org_unit_in.dict()
    org_unit_data['tenant_id'] = ctx.tenant_id
    org_unit_data['path'] = _build_path(parent_path, org_unit_in.name)
    
    org_unit = OrgUnit(**org_unit_data)
    session.add(org_unit)
    session.commit()
    session.refresh(org_unit)
    
    return OrgUnitRead.from_orm(org_unit)


@router.get("/", response_model=List[OrgUnitRead])
def list_org_units(
    parent_id: Optional[str] = Query(None, description="Filter by parent org"),
    active: Optional[bool] = Query(None),
    echelon: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session: Session = Depends(get_session),
    ctx: TenantContext = Depends(TenantContext)
) -> List[OrgUnitRead]:
    """List organization units in the current tenant."""
    statement = select(OrgUnit).where(OrgUnit.tenant_id == ctx.tenant_id)
    
    if parent_id is not None:
        statement = statement.where(OrgUnit.parent_id == parent_id)
    if active is not None:
        statement = statement.where(OrgUnit.active == active)
    if echelon:
        statement = statement.where(OrgUnit.echelon == echelon)
    
    # Order by path for hierarchical display
    statement = statement.order_by(OrgUnit.path).offset(skip).limit(limit)
    org_units = session.exec(statement).all()
    
    # Add user counts
    results = []
    for org_unit in org_units:
        org_read = OrgUnitRead.from_orm(org_unit)
        org_read.user_count = len(org_unit.users)
        results.append(org_read)
    
    return results


@router.get("/tree", response_model=List[OrgUnitRead])
def get_org_tree(
    root_id: Optional[str] = Query(None, description="Root org unit ID"),
    session: Session = Depends(get_session),
    ctx: TenantContext = Depends(TenantContext)
) -> List[OrgUnitRead]:
    """Get organization tree structure."""
    if root_id:
        root = session.get(OrgUnit, root_id)
        ctx.check_access(root)
        # Get all descendants
        statement = select(OrgUnit).where(
            and_(
                OrgUnit.tenant_id == ctx.tenant_id,
                OrgUnit.path.startswith(root.path)
            )
        )
    else:
        # Get all org units
        statement = select(OrgUnit).where(OrgUnit.tenant_id == ctx.tenant_id)
    
    statement = statement.order_by(OrgUnit.path)
    org_units = session.exec(statement).all()
    
    return [OrgUnitRead.from_orm(org) for org in org_units]


@router.get("/{org_unit_id}", response_model=OrgUnitRead)
def get_org_unit(
    org_unit_id: str,
    session: Session = Depends(get_session),
    ctx: TenantContext = Depends(TenantContext)
) -> OrgUnitRead:
    """Get organization unit details."""
    org_unit = session.get(OrgUnit, org_unit_id)
    ctx.check_access(org_unit)
    
    org_read = OrgUnitRead.from_orm(org_unit)
    org_read.user_count = len(org_unit.users)
    
    return org_read


@router.patch("/{org_unit_id}", response_model=OrgUnitRead)
def update_org_unit(
    org_unit_id: str,
    org_unit_update: OrgUnitUpdate,
    session: Session = Depends(get_session),
    ctx: TenantContext = Depends(TenantContext)
) -> OrgUnitRead:
    """Update organization unit. Admin only."""
    if not ctx.current_user.is_tenant_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    org_unit = session.get(OrgUnit, org_unit_id)
    ctx.check_access(org_unit)
    
    update_data = org_unit_update.dict(exclude_unset=True)
    
    # If changing parent, update path
    if 'parent_id' in update_data:
        parent_path = None
        if update_data['parent_id']:
            parent = session.get(OrgUnit, update_data['parent_id'])
            ctx.check_access(parent)
            parent_path = parent.path
            
            # Prevent circular references
            if org_unit.path in parent_path:
                raise HTTPException(
                    status_code=400, 
                    detail="Cannot set descendant as parent"
                )
        
        # Update this org unit's path and all descendants
        old_path = org_unit.path
        new_path = _build_path(parent_path, org_unit.name)
        
        # Update all descendants
        descendants = session.exec(
            select(OrgUnit).where(
                and_(
                    OrgUnit.tenant_id == ctx.tenant_id,
                    OrgUnit.path.startswith(old_path),
                    OrgUnit.id != org_unit_id
                )
            )
        ).all()
        
        for desc in descendants:
            desc.path = desc.path.replace(old_path, new_path, 1)
            session.add(desc)
        
        org_unit.path = new_path
    
    # Apply other updates
    for field, value in update_data.items():
        if field != 'parent_id' or value != org_unit.parent_id:
            setattr(org_unit, field, value)
    
    session.add(org_unit)
    session.commit()
    session.refresh(org_unit)
    
    return OrgUnitRead.from_orm(org_unit)


@router.delete("/{org_unit_id}")
def delete_org_unit(
    org_unit_id: str,
    force: bool = Query(False, description="Force delete even with users"),
    session: Session = Depends(get_session),
    ctx: TenantContext = Depends(TenantContext)
) -> dict:
    """Delete organization unit. Admin only."""
    if not ctx.current_user.is_tenant_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    org_unit = session.get(OrgUnit, org_unit_id)
    ctx.check_access(org_unit)
    
    # Check for users
    user_count = session.exec(
        select(User).where(User.org_unit_id == org_unit_id)
    ).count()
    
    if user_count > 0 and not force:
        raise HTTPException(
            status_code=400,
            detail=f"Org unit has {user_count} users. Use force=true to delete anyway."
        )
    
    # Check for child org units
    child_count = session.exec(
        select(OrgUnit).where(OrgUnit.parent_id == org_unit_id)
    ).count()
    
    if child_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Org unit has {child_count} child organizations. Delete them first."
        )
    
    # Soft delete by marking inactive
    org_unit.active = False
    session.add(org_unit)
    session.commit()
    
    return {"message": f"Org unit '{org_unit.name}' deactivated"}