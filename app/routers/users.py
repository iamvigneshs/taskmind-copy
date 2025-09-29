# Copyright (c) 2025 Acarin Inc. All rights reserved.
# Proprietary and confidential.
"""User management API routes."""
from __future__ import annotations

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, and_

from app.database import get_session
from app.models import User, OrgUnit
from app.schemas import UserCreate, UserRead, UserUpdate
from app.dependencies import get_current_user, get_current_tenant, require_tenant_admin

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserRead)
def create_user(
    user_in: UserCreate,
    session: Session = Depends(get_session),
    current_user = Depends(require_tenant_admin),
    tenant_id: str = Depends(get_current_tenant)
) -> UserRead:
    """Create a new user in the current tenant."""
    # Check if UPN already exists in tenant
    existing = session.exec(
        select(User).where(
            and_(User.tenant_id == tenant_id, User.upn == user_in.upn)
        )
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"User with UPN '{user_in.upn}' already exists")
    
    # Verify org unit exists and belongs to tenant
    org_unit = session.get(OrgUnit, user_in.org_unit_id)
    if not org_unit or org_unit.tenant_id != tenant_id:
        raise HTTPException(status_code=400, detail="Invalid organization unit")
    
    # Create user
    user_data = user_in.dict(exclude={'password'})
    user_data['tenant_id'] = tenant_id
    user = User(**user_data)
    
    # TODO: Hash password if provided
    # if user_in.password:
    #     user.password_hash = hash_password(user_in.password)
    
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return UserRead.from_orm(user)


@router.get("/", response_model=List[UserRead])
def list_users(
    org_unit_id: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    is_available: Optional[bool] = Query(None),
    search: Optional[str] = Query(None, description="Search in name or UPN"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
) -> List[UserRead]:
    """List users in the current tenant."""
    statement = select(User).where(User.tenant_id == tenant_id)
    
    if org_unit_id:
        statement = statement.where(User.org_unit_id == org_unit_id)
    if is_active is not None:
        statement = statement.where(User.is_active == is_active)
    if is_available is not None:
        statement = statement.where(User.is_available == is_available)
    if search:
        search_term = f"%{search}%"
        statement = statement.where(
            (User.name.ilike(search_term)) | (User.upn.ilike(search_term))
        )
    
    statement = statement.offset(skip).limit(limit)
    users = session.exec(statement).all()
    
    return [UserRead.from_orm(u) for u in users]


@router.get("/me", response_model=UserRead)
def get_current_user_profile(
    current_user = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> UserRead:
    """Get current user's profile."""
    session.refresh(current_user)
    return UserRead.from_orm(current_user)


@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: str,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
) -> UserRead:
    """Get user details."""
    user = session.get(User, user_id)
    if not user or user.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserRead.from_orm(user)


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: str,
    user_update: UserUpdate,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
) -> UserRead:
    """Update user. Users can update some of their own fields, admins can update any user."""
    user = session.get(User, user_id)
    if not user or user.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check permissions
    if current_user.id == user_id:
        # Users can update their own profile (limited fields)
        allowed_self_update = {
            'name', 'phone', 'office_symbol', 'is_available', 'out_of_office_until'
        }
        update_data = user_update.dict(exclude_unset=True)
        restricted_updates = set(update_data.keys()) - allowed_self_update
        if restricted_updates and not current_user.is_tenant_admin:
            raise HTTPException(
                status_code=403,
                detail=f"Cannot self-update fields: {restricted_updates}"
            )
    elif not current_user.is_tenant_admin:
        raise HTTPException(status_code=403, detail="Only admins can update other users")
    
    # Verify new org unit if changing
    update_data = user_update.dict(exclude_unset=True)
    if 'org_unit_id' in update_data:
        org_unit = session.get(OrgUnit, update_data['org_unit_id'])
        if not org_unit or org_unit.tenant_id != tenant_id:
            raise HTTPException(status_code=400, detail="Invalid organization unit")
    
    # Apply updates
    for field, value in update_data.items():
        setattr(user, field, value)
    
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return UserRead.from_orm(user)


@router.post("/{user_id}/deactivate", response_model=UserRead)
def deactivate_user(
    user_id: str,
    session: Session = Depends(get_session),
    current_user = Depends(require_tenant_admin),
    tenant_id: str = Depends(get_current_tenant)
) -> UserRead:
    """Deactivate a user. Tenant admin only."""
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    
    user = session.get(User, user_id)
    if not user or user.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = False
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return UserRead.from_orm(user)


@router.post("/{user_id}/activate", response_model=UserRead)
def activate_user(
    user_id: str,
    session: Session = Depends(get_session),
    current_user = Depends(require_tenant_admin),
    tenant_id: str = Depends(get_current_tenant)
) -> UserRead:
    """Activate a user. Tenant admin only."""
    user = session.get(User, user_id)
    if not user or user.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = True
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return UserRead.from_orm(user)