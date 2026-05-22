from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database_sqlalchemy import get_db
from dependencies.admin_auth import role_required
from models.settings import SystemSetting
from pydantic import BaseModel
from typing import Dict, Any

router = APIRouter(prefix="/admin/settings", tags=["Admin Settings"])

class SettingsUpdate(BaseModel):
    settings: Dict[str, str]

@router.get("")
async def get_settings(
    db: Session = Depends(get_db),
    admin: dict = Depends(role_required(["SUPER_ADMIN"]))
):
    """
    Get all system settings grouped by category.
    """
    try:
        settings_db = db.query(SystemSetting).all()
        # Initialize with defaults if table is empty
        if not settings_db:
            default_settings = [
                SystemSetting(key="platform_name", value="Laborgro", category="general"),
                SystemSetting(key="support_email", value="support@laborgro.in", category="general"),
                SystemSetting(key="default_language", value="English", category="general"),
                SystemSetting(key="default_city", value="Bangalore", category="general"),
                
                SystemSetting(key="session_timeout", value="60", category="security"),
                SystemSetting(key="max_login_attempts", value="5", category="security"),
                SystemSetting(key="admin_2fa", value="Disabled", category="security"),
                
                SystemSetting(key="platform_fee", value="15", category="payments"),
                SystemSetting(key="min_payout", value="500", category="payments"),
                SystemSetting(key="payout_schedule", value="Weekly", category="payments"),
                SystemSetting(key="payment_gateway", value="Razorpay", category="payments"),
                
                SystemSetting(key="notify_new_booking", value="true", category="notifications"),
                SystemSetting(key="notify_dispute", value="true", category="notifications"),
                SystemSetting(key="notify_kyc", value="true", category="notifications"),
                SystemSetting(key="notify_error", value="true", category="notifications"),
                SystemSetting(key="notify_weekly", value="false", category="notifications"),
            ]
            db.add_all(default_settings)
            db.commit()
            settings_db = default_settings
            
        settings_dict = {s.key: s.value for s in settings_db}
        return settings_dict
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("")
async def update_settings(
    req: SettingsUpdate,
    db: Session = Depends(get_db),
    admin: dict = Depends(role_required(["SUPER_ADMIN"]))
):
    """
    Update system settings.
    """
    try:
        for key, value in req.settings.items():
            setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
            if setting:
                setting.value = value
            else:
                # Fallback category to general if unknown
                db.add(SystemSetting(key=key, value=value, category="general"))
        db.commit()
        return {"status": "success", "message": "Settings updated"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
