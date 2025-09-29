# Copyright (c) 2025 Acarin Inc. All rights reserved.
# Proprietary and confidential.
"""FastAPI dependencies for authentication and authorization."""
from __future__ import annotations

from typing import Optional
from datetime import datetime
from fastapi import Depends, HTTPException, Header, status
from sqlmodel import Session, select

from app.database import get_session
from app.models import User, Tenant, TenantStatus


# Mock authentication for development
# TODO: Replace with real JWT authentication
async def get_current_user_id(
    x_user_id: Optional[str] = Header(None, description="User ID for development"),
    authorization: Optional[str] = Header(None, description="Bearer token")
) -> str:
    """Get current user ID from headers."""
    # For development, use header
    if x_user_id:
        return x_user_id
    
    # TODO: Implement JWT token validation
    # if authorization:
    #     token = authorization.replace("Bearer ", "")
    #     payload = validate_jwt(token)
    #     return payload["user_id"]
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session)
) -> User:
    """Get current user object."""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is deactivated"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    session.add(user)
    session.commit()
    
    return user


async def get_current_tenant(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> str:
    """Get current tenant ID and verify it's active."""
    tenant = session.get(Tenant, current_user.tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Tenant configuration error"
        )
    
    if tenant.status != TenantStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Tenant is {tenant.status}"
        )
    
    return tenant.id


async def require_tenant_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """Require current user to be a tenant admin."""
    if not current_user.is_tenant_admin and not current_user.is_system_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant admin access required"
        )
    return current_user


async def require_system_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """Require current user to be a system admin."""
    if not current_user.is_system_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="System admin access required"
        )
    return current_user


class TenantContext:
    """Dependency to inject tenant context into operations."""
    
    def __init__(
        self,
        tenant_id: str = Depends(get_current_tenant),
        current_user: User = Depends(get_current_user)
    ):
        self.tenant_id = tenant_id
        self.current_user = current_user
    
    def filter_query(self, query, model):
        """Add tenant filter to a query."""
        if hasattr(model, 'tenant_id'):
            return query.where(model.tenant_id == self.tenant_id)
        return query
    
    def check_access(self, obj, field='tenant_id'):
        """Check if object belongs to current tenant."""
        if not obj:
            raise HTTPException(status_code=404, detail="Not found")
        if hasattr(obj, field) and getattr(obj, field) != self.tenant_id:
            raise HTTPException(status_code=404, detail="Not found")
        return obj


# Development helpers
async def get_or_create_dev_tenant(
    session: Session = Depends(get_session)
) -> Tenant:
    """Get or create a development tenant."""
    tenant = session.exec(
        select(Tenant).where(Tenant.name == "dev-tenant")
    ).first()
    
    if not tenant:
        from app.models import TenantType, ClassificationLevel
        tenant = Tenant(
            name="dev-tenant",
            display_name="Development Tenant",
            tenant_type=TenantType.MILITARY,
            status=TenantStatus.ACTIVE,
            allowed_classification_levels=[
                ClassificationLevel.UNCLASSIFIED,
                ClassificationLevel.CONFIDENTIAL,
                ClassificationLevel.SECRET
            ]
        )
        session.add(tenant)
        session.commit()
        session.refresh(tenant)
    
    return tenant


async def get_or_create_dev_user(
    tenant: Tenant = Depends(get_or_create_dev_tenant),
    session: Session = Depends(get_session)
) -> User:
    """Get or create a development user."""
    # First ensure we have an org unit
    from app.models import OrgUnit, EchelonLevel
    org_unit = session.exec(
        select(OrgUnit).where(
            (OrgUnit.tenant_id == tenant.id) & 
            (OrgUnit.name == "Dev HQ")
        )
    ).first()
    
    if not org_unit:
        org_unit = OrgUnit(
            tenant_id=tenant.id,
            name="Dev HQ",
            short_name="DEVHQ",
            echelon=EchelonLevel.HQDA,
            path="/devhq"
        )
        session.add(org_unit)
        session.commit()
        session.refresh(org_unit)
    
    # Now get or create user
    user = session.exec(
        select(User).where(
            (User.tenant_id == tenant.id) &
            (User.upn == "dev@missionmind.local")
        )
    ).first()
    
    if not user:
        from app.models import ClassificationLevel
        user = User(
            tenant_id=tenant.id,
            upn="dev@missionmind.local",
            name="Dev User",
            org_unit_id=org_unit.id,
            clearance_level=ClassificationLevel.SECRET,
            is_tenant_admin=True,
            is_active=True,
            roles=["admin", "user"]
        )
        session.add(user)
        session.commit()
        session.refresh(user)
    
    return user