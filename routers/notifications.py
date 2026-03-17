from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from dependencies.auth import get_current_user
from services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("", response_model=List[Dict[str, Any]])
async def get_my_notifications(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Fetch in-app notifications for the logged-in user.
    """
    return await NotificationService.get_user_notifications(current_user["id"])

@router.put("/{notification_id}/read")
async def mark_as_read(
    notification_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Mark a specific notification as seen.
    """
    success = await NotificationService.mark_read(notification_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"status": "success"}
