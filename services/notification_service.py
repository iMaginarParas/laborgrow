from typing import List, Dict, Any, Optional
from repositories.notification_repository import NotificationRepository

class NotificationService:
    _repo = NotificationRepository()

    @staticmethod
    async def create_notification(user_id: str, title: str, message: str, type: str = "general") -> Dict[str, Any]:
        """
        Creates an in-app notification for a developer or worker.
        """
        data = {
            "user_id": user_id,
            "title": title,
            "message": message,
            "type": type,
            "is_read": False
        }
        try:
            return await NotificationService._repo.insert(data)
        except Exception as e:
            # If the table doesn't exist, log it and don't crash
            print(f"FAILED TO SEND NOTIFICATION: {e}")
            return None

    @staticmethod
    async def get_user_notifications(user_id: str) -> List[Dict[str, Any]]:
        return await NotificationService._repo.list_by_user(user_id)

    @staticmethod
    async def mark_read(notification_id: str) -> bool:
        return await NotificationService._repo.mark_as_read(notification_id)
