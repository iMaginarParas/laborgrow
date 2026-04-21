from typing import List, Dict, Any
from repositories.base_repository import BaseRepository

class NotificationRepository(BaseRepository):
    def __init__(self):
        super().__init__("notifications")

    async def list_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        result = self.get_client().table(self.table_name)\
            .select("*")\
            .eq("user_id", str(user_id))\
            .order("created_at", desc=True)\
            .execute()
        return result.data or []

    async def mark_as_read(self, notification_id: str) -> bool:
        result = self.get_client().table(self.table_name)\
            .update({"is_read": True})\
            .eq("id", notification_id)\
            .execute()
        return len(result.data) > 0 if result.data else False
