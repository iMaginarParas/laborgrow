from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime
from typing import List, Optional

# --- CORE USER SCHEMAS ---
class UserBase(BaseModel):
    name: str
    email: EmailStr
    phone: str
    profile_pic_url: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: UUID
    created_at: datetime
    class Config:
        from_attributes = True

# --- AUTHENTICATION SCHEMAS ---
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class LoginRequest(BaseModel):
    phone_or_email: str
    password: str

# --- SERVICE CATEGORY SCHEMAS ---
class CategoryBase(BaseModel):
    name: str
    emoji: str
    slug: str

class CategoryResponse(CategoryBase):
    id: int
    class Config:
        from_attributes = True

# --- WORKER SCHEMAS ---
class WorkerSkillBase(BaseModel):
    skill_name: str

class WorkerBase(BaseModel):
    bio: Optional[str] = None
    city: str
    lat: float
    lng: float
    experience_years: int
    hourly_rate: float
    min_hours: int = 1

class WorkerResponse(WorkerBase):
    id: UUID
    user: UserResponse
    is_verified: bool
    is_available: bool
    rating: float
    categories: List[CategoryResponse]
    skills: List[WorkerSkillBase]
    class Config:
        from_attributes = True

# --- BOOKING SCHEMAS ---
class BookingCreate(BaseModel):
    worker_id: UUID
    category_id: int
    booking_date: str
    time_slot: str
    hours: int
    address: str

class BookingResponse(BaseModel):
    id: UUID
    worker: WorkerResponse
    booking_date: str
    time_slot: str
    hours: int
    address: str
    total_amount: float
    platform_fee: float
    discount_amount: float
    status: str
    booking_ref: str
    created_at: datetime
    class Config:
        from_attributes = True

# --- REVIEW SCHEMAS ---
class ReviewCreate(BaseModel):
    booking_id: UUID
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None

class ReviewResponse(ReviewCreate):
    id: UUID
    customer: UserResponse
    created_at: datetime
    class Config:
        from_attributes = True
