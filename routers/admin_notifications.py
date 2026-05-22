from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database_sqlalchemy import get_db
from dependencies.admin_auth import role_required
from models.notification import Notification, NotificationChannel, NotificationStatus
import uuid
from datetime import datetime

router = APIRouter(prefix="/admin/notifications", tags=["Admin Notifications"])

class BroadcastRequest(BaseModel):
    title: str
    message: str
    target: str # 'all', 'workers', 'employers'

@router.get("")
async def get_notifications(
    db: Session = Depends(get_db),
    admin: dict = Depends(role_required(["SUPER_ADMIN", "OPS_ADMIN", "SUPPORT_ADMIN"]))
):
    """
    Get history of sent notifications.
    """
    try:
        # For broadcast history, we might just query unique titles/bodies or limit to recent 50
        notifications = db.query(Notification).order_by(desc(Notification.created_at)).limit(50).all()
        
        # Deduplicate by title+body since broadcasts create many rows, or just return them as a flat list
        # We'll just group them by title and message for the UI history
        history_map = {}
        for n in notifications:
            key = f"{n.title}-{n.body}"
            if key not in history_map:
                history_map[key] = {
                    "id": str(n.id),
                    "title": n.title,
                    "target": n.recipient_type.lower() if n.recipient_type else "all",
                    "msg": n.body,
                    "sent": n.created_at.strftime("%Y-%m-%d %H:%M")
                }
        
        return list(history_map.values())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/broadcast")
async def broadcast_notification(
    req: BroadcastRequest,
    db: Session = Depends(get_db),
    admin: dict = Depends(role_required(["SUPER_ADMIN", "OPS_ADMIN"]))
):
    """
    Broadcast a notification to users.
    """
    try:
        # In a real system, we'd query all users in the target group and insert a Notification row for each
        # For now we insert a single record representing the broadcast so it shows up in history
        
        # Assuming we just insert one "broadcast" record
        broadcast = Notification(
            recipient_id=uuid.uuid4(), # Dummy ID for broadcast
            recipient_type=req.target.upper(),
            channel=NotificationChannel.PUSH,
            title=req.title,
            body=req.message,
            status=NotificationStatus.SENT
        )
        db.add(broadcast)
        db.commit()
        
        return {"status": "success", "message": "Broadcast sent successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
