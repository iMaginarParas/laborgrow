from pydantic import BaseModel, EmailStr, Field, field_validator
from uuid import UUID
from datetime import datetime
from typing import List, Optional, Any

# --- CORE USER SCHEMAS ---
class UserBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=15)
    profile_pic_url: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")
    role: Optional[str] = "employee"

class UserResponse(BaseModel):
    """
    Lenient response schema — DB rows may have blank/missing phone numbers
    so we do not enforce min_length on output to avoid ResponseValidationError.
    """
    id: UUID
    name: str = "Worker"
    email: str = ""
    phone: str = ""
    profile_pic_url: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    created_at: Optional[datetime] = None

    @field_validator("name", mode="before")
    @classmethod
    def coerce_blank_name(cls, v):
        return v if v and str(v).strip() else "Worker"

    @field_validator("email", "phone", mode="before")
    @classmethod
    def coerce_none_to_str(cls, v):
        return v if v is not None else ""

    class Config:
        from_attributes = True

# --- AUTHENTICATION SCHEMAS ---
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class LoginRequest(BaseModel):
    phone_or_email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=1)

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
    city: str = ""
    lat: Optional[float] = 0.0
    lng: Optional[float] = 0.0
    experience_years: Optional[int] = 0
    hourly_rate: Optional[float] = 0.0
    min_hours: int = 1

class WorkerResponse(WorkerBase):
    id: UUID
    user: Optional[UserResponse] = None
    is_verified: Optional[bool] = False
    is_available: Optional[bool] = True
    rating: Optional[float] = 0.0
    categories: List[CategoryResponse] = []
    skills: List[WorkerSkillBase] = []
    message: Optional[str] = None
    simulated: Optional[bool] = False

    @field_validator("categories", "skills", mode="before")
    @classmethod
    def coerce_none_to_list(cls, v):
        if v is None:
            return []
        return v

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
    message: Optional[str] = None
    simulated: Optional[bool] = False
    class Config:
        from_attributes = True

# --- REVIEW SCHEMAS ---
class ReviewCreate(BaseModel):
    worker_id: UUID
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None

class ReviewResponse(ReviewCreate):
    id: UUID
    customer: UserResponse
    created_at: datetime
    class Config:
        from_attributes = True

# --- JOB SCHEMAS ---
class JobCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., min_length=5)
    category_id: int
    job_city: str
    salary_min: Optional[float] = 0.0
    salary_max: Optional[float] = 0.0
    lat: Optional[float] = 0.0
    lng: Optional[float] = 0.0
    openings: Optional[int] = 1

class JobResponse(JobCreate):
    id: Any
    employer_id: Any
    status: str = "open"
    created_at: datetime
    category: Optional[CategoryResponse] = None
    class Config:
        from_attributes = True

# --- JOB APPLICATION SCHEMAS ---
class ApplicationCreate(BaseModel):
    job_id: UUID

class ApplicationResponse(BaseModel):
    id: Any
    job_id: Any
    worker_id: Any
    status: str # pending, accepted, rejected
    created_at: datetime
    worker: Optional[WorkerResponse] = None
    job: Optional[JobResponse] = None
    class Config:
        from_attributes = True
