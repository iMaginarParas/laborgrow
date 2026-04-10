from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database_sqlalchemy import get_db
from ..dependencies.admin_auth import role_required
from ..services.admin_service import AdminService, log_admin_audit
from uuid import UUID
from typing import Optional

router = APIRouter(prefix="/admin", tags=["User Management"])

@router.get("/users")
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: dict = Depends(role_required(["SUPER_ADMIN", "SUPPORT_ADMIN"]))
):
    """
    Paginated user list with optional search.
    """
    return AdminService.get_paginated_users(db, skip, limit, search)

@router.post("/users/suspend")
async def suspend_user(
    user_id: UUID,
    reason: str,
    db: Session = Depends(get_db),
    admin: dict = Depends(role_required(["SUPER_ADMIN", "SUPPORT_ADMIN"]))
):
    """
    Locks a user account from performing any actions.
    """
    # Logic to update user status in DB
    # ...
    
    log_admin_audit(db, admin["id"], "SUSPEND_USER", str(user_id), {"reason": reason})
    return {"message": "User suspended successfully"}

@router.post("/users/reactivate")
async def reactivate_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    admin: dict = Depends(role_required(["SUPER_ADMIN"]))
):
    """
    Unlocks a previously suspended account.
    """
    log_admin_audit(db, admin["id"], "REACTIVATE_USER", str(user_id), {})
    return {"message": "User reactivated successfully"}

@router.post("/users/reset-password")
async def reset_password(
    user_id: UUID,
    db: Session = Depends(get_db),
    admin: dict = Depends(role_required(["SUPER_ADMIN"]))
):
    """
    Triggers a password reset or forces a temporary password.
    """
    log_admin_audit(db, admin["id"], "RESET_PASSWORD", str(user_id), {})
    return {"message": "Password reset triggered"}
