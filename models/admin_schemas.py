from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import datetime

class AdminLogin(BaseModel):
    email: EmailStr
    password: str

class AdminUserResponse(BaseModel):
    id: UUID
    email: EmailStr
    role: str
    is_active: bool
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: AdminUserResponse
