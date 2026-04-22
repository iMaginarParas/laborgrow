from database import get_supabase
from typing import List, Dict, Any

class ChatService:
    @staticmethod
    async def get_messages(user_id: str, other_user_id: str) -> List[Dict[str, Any]]:
        supabase = get_supabase()
        response = supabase.table("chat_messages").select("*").or_(
            f"and(sender_id.eq.{user_id},receiver_id.eq.{other_user_id}),"
            f"and(sender_id.eq.{other_user_id},receiver_id.eq.{user_id})"
        ).order("created_at", desc=False).execute()
        return response.data

    @staticmethod
    async def send_message(sender_id: str, receiver_id: str, content: str) -> Dict[str, Any]:
        supabase = get_supabase()
        
        # Insert message
        data = {
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "content": content
        }
        res = supabase.table("chat_messages").insert(data).execute()
        
        # Create a notification for the receiver
        notif_data = {
            "user_id": receiver_id,
            "title": "New Message",
            "message": f"You received a new message.",
            "type": "message",
            "link_id": sender_id
        }
        try:
            supabase.table("notifications").insert(notif_data).execute()
        except Exception as e:
            print(f"Failed to create notification: {e}")
            
        return res.data[0] if res.data else None
