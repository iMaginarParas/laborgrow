from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database_sqlalchemy import get_db
from ..dependencies.admin_auth import role_required
from ..services.admin_service import AdminService, log_admin_audit
from ..services.worker_service import WorkerService # Assuming existing service
from uuid import UUID
from typing import Optional

router = APIRouter(prefix="/admin", tags=["Worker Management"])

@router.get("/workers")
async def get_workers(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: dict = Depends(role_required(["SUPER_ADMIN", "OPS_ADMIN"]))
):
    return AdminService.get_paginated_workers(db, skip, limit, search)

@router.post("/workers/approve")
async def approve_worker(
    worker_id: UUID,
    db: Session = Depends(get_db),
    admin: dict = Depends(role_required(["SUPER_ADMIN", "OPS_ADMIN"]))
):
    """
    Approves a worker after verification.
    """
    # result = await WorkerService.update_profile(str(worker_id), {"is_verified": True})
    
    log_admin_audit(db, admin["id"], "APPROVE_WORKER", str(worker_id), {})
    return {"message": "Worker approved"}

@router.post("/workers/reject")
async def reject_worker(
    worker_id: UUID,
    reason: str,
    db: Session = Depends(get_db),
    admin: dict = Depends(role_required(["SUPER_ADMIN", "OPS_ADMIN"]))
):
    log_admin_audit(db, admin["id"], "REJECT_WORKER", str(worker_id), {"reason": reason})
    return {"message": "Worker rejected"}

@router.post("/workers/suspend")
async def suspend_worker(
    worker_id: UUID,
    reason: str,
    db: Session = Depends(get_db),
    admin: dict = Depends(role_required(["SUPER_ADMIN"]))
):
    log_admin_audit(db, admin["id"], "SUSPEND_WORKER", str(worker_id), {"reason": reason})
    return {"message": "Worker suspended"}
