from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from dependencies.auth import get_current_user
from services.chat_service import ChatService
from pydantic import BaseModel

router = APIRouter(prefix="/chat", tags=["Chat"])

class SendMessageRequest(BaseModel):
    receiver_id: str
    content: str

@router.get("/{other_user_id}", response_model=List[Dict[str, Any]])
async def get_messages(
    other_user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    try:
        data = await ChatService.get_messages(current_user["id"], other_user_id)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("", response_model=Dict[str, Any])
async def send_message(
    req: SendMessageRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    try:
        data = await ChatService.send_message(
            sender_id=current_user["id"],
            receiver_id=req.receiver_id,
            content=req.content
        )
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
