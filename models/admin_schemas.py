from pydantic import BaseModel, EmailStr
from typing import Optional, List
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

class AdminCreateWorkerRequest(BaseModel):
    full_name: str
    phone: str
    email: Optional[str] = ""
    city: Optional[str] = "Mumbai"
    hourly_rate: Optional[float] = 500.0
    experience_years: Optional[int] = 0
    skills: Optional[List[str]] = []
    bio: Optional[str] = ""
    is_verified: Optional[bool] = True
    is_available: Optional[bool] = True
    category_ids: Optional[List[int]] = [1]

