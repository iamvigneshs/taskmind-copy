# Copyright (c) 2025 Acarin Inc. All rights reserved.
# Proprietary and confidential.
"""Tenant management API routes."""
from __future__ import annotations

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.database import get_session
from app.models import Tenant, TenantStatus
from app.schemas import TenantCreate, TenantRead, TenantUpdate
from app.dependencies import get_current_user, require_system_admin

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.post("/", response_model=TenantRead, dependencies=[Depends(require_system_admin)])
def create_tenant(
    tenant_in: TenantCreate,
    session: Session = Depends(get_session)
) -> TenantRead:
    """Create a new tenant organization. System admin only."""
    # Check if tenant name already exists
    existing = session.exec(
        select(Tenant).where(Tenant.name == tenant_in.name)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Tenant name '{tenant_in.name}' already exists")
    
    # Create tenant
    tenant = Tenant(**tenant_in.dict())
    session.add(tenant)
    session.commit()
    session.refresh(tenant)
    
    return TenantRead.from_orm(tenant)


@router.get("/", response_model=List[TenantRead], dependencies=[Depends(require_system_admin)])
def list_tenants(
    status: Optional[TenantStatus] = Query(None),
    tenant_type: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session: Session = Depends(get_session)
) -> List[TenantRead]:
    """List all tenants. System admin only."""
    statement = select(Tenant)
    
    if status:
        statement = statement.where(Tenant.status == status)
    if tenant_type:
        statement = statement.where(Tenant.tenant_type == tenant_type)
    
    statement = statement.offset(skip).limit(limit)
    tenants = session.exec(statement).all()
    
    return [TenantRead.from_orm(t) for t in tenants]


@router.get("/{tenant_id}", response_model=TenantRead)
def get_tenant(
    tenant_id: str,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
) -> TenantRead:
    """Get tenant details. Users can only view their own tenant."""
    tenant = session.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Check access
    if not current_user.is_system_admin and current_user.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get statistics
    tenant_read = TenantRead.from_orm(tenant)
    tenant_read.user_count = len(tenant.users)
    tenant_read.task_count = len(tenant.tasks)
    
    return tenant_read


@router.patch("/{tenant_id}", response_model=TenantRead)
def update_tenant(
    tenant_id: str,
    tenant_update: TenantUpdate,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
) -> TenantRead:
    """Update tenant. Tenant admins can update some fields, system admins can update all."""
    tenant = session.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Check permissions
    if current_user.is_system_admin:
        # System admin can update everything
        pass
    elif current_user.is_tenant_admin and current_user.tenant_id == tenant_id:
        # Tenant admin can only update certain fields
        restricted_fields = {'status', 'max_users', 'max_storage_gb'}
        update_data = tenant_update.dict(exclude_unset=True)
        if any(field in update_data for field in restricted_fields):
            raise HTTPException(
                status_code=403, 
                detail=f"Tenant admins cannot update: {restricted_fields}"
            )
    else:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Apply updates
    update_data = tenant_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tenant, field, value)
    
    session.add(tenant)
    session.commit()
    session.refresh(tenant)
    
    return TenantRead.from_orm(tenant)


@router.post("/{tenant_id}/activate", response_model=TenantRead, dependencies=[Depends(require_system_admin)])
def activate_tenant(
    tenant_id: str,
    session: Session = Depends(get_session)
) -> TenantRead:
    """Activate a pending tenant. System admin only."""
    tenant = session.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    if tenant.status != TenantStatus.PENDING:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot activate tenant in status: {tenant.status}"
        )
    
    tenant.status = TenantStatus.ACTIVE
    tenant.activated_at = datetime.utcnow()
    
    session.add(tenant)
    session.commit()
    session.refresh(tenant)
    
    return TenantRead.from_orm(tenant)


@router.post("/{tenant_id}/suspend", response_model=TenantRead, dependencies=[Depends(require_system_admin)])
def suspend_tenant(
    tenant_id: str,
    reason: str = Query(..., description="Reason for suspension"),
    session: Session = Depends(get_session)
) -> TenantRead:
    """Suspend a tenant. System admin only."""
    tenant = session.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    if tenant.status != TenantStatus.ACTIVE:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot suspend tenant in status: {tenant.status}"
        )
    
    tenant.status = TenantStatus.SUSPENDED
    if not tenant.settings:
        tenant.settings = {}
    tenant.settings['suspension_reason'] = reason
    tenant.settings['suspended_at'] = datetime.utcnow().isoformat()
    
    session.add(tenant)
    session.commit()
    session.refresh(tenant)
    
    return TenantRead.from_orm(tenant)