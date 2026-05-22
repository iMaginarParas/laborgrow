from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database_sqlalchemy import get_db
from dependencies.admin_auth import role_required
from models.dispute import Dispute, DisputeStatus
import uuid

router = APIRouter(prefix="/admin/disputes", tags=["Admin Disputes"])

@router.get("")
async def get_all_disputes(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: str = Query("", description="Search by booking ID or reported by"),
    db: Session = Depends(get_db),
    admin: dict = Depends(role_required(["SUPER_ADMIN", "OPS_ADMIN", "SUPPORT_ADMIN"]))
):
    """
    List all disputes with pagination and optional search.
    """
    try:
        query = db.query(Dispute)
        
        if search:
            # simple search by checking if search string is in booking_id (converted to str)
            search_term = f"%{search}%"
            query = query.filter(
                (Dispute.booking_id.cast(str).ilike(search_term)) |
                (Dispute.reported_by.cast(str).ilike(search_term))
            )
            
        total = query.count()
        disputes = query.order_by(desc(Dispute.created_at)).offset(skip).limit(limit).all()
        
        # Format the response
        formatted_disputes = []
        for d in disputes:
            formatted_disputes.append({
                "id": str(d.id),
                "booking": str(d.booking_id),
                "reportedBy": f"User {str(d.reported_by)[:8]}", # Mock name resolution for now
                "status": d.status.value if hasattr(d.status, 'value') else d.status,
                "priority": "High" if d.status == DisputeStatus.ESCALATED else "Medium",
                "date": d.created_at.strftime("%Y-%m-%d")
            })
            
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "data": formatted_disputes
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{dispute_id}/resolve")
async def resolve_dispute(
    dispute_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: dict = Depends(role_required(["SUPER_ADMIN", "OPS_ADMIN", "SUPPORT_ADMIN"]))
):
    """
    Mark a dispute as resolved.
    """
    try:
        dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
        if not dispute:
            raise HTTPException(status_code=404, detail="Dispute not found")
            
        dispute.status = DisputeStatus.RESOLVED
        db.commit()
        
        return {"status": "success", "message": "Dispute resolved successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{dispute_id}/escalate")
async def escalate_dispute(
    dispute_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: dict = Depends(role_required(["SUPER_ADMIN", "OPS_ADMIN"]))
):
    """
    Escalate a dispute.
    """
    try:
        dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
        if not dispute:
            raise HTTPException(status_code=404, detail="Dispute not found")
            
        dispute.status = DisputeStatus.ESCALATED
        db.commit()
        
        return {"status": "success", "message": "Dispute escalated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
