import os
import re
from typing import Optional, List
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from supabase import create_client, Client
import googlemaps

load_dotenv()

# ── Configuration ──────────────────────────────────────────────────────────────
SUPABASE_URL         = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
GOOGLE_MAPS_API_KEY  = os.environ.get("GOOGLE_MAPS_API_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
gmaps             = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
security          = HTTPBearer()

app = FastAPI(title="LaborGrow API", version="2.3.0")

# ── CORS ───────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mount admin router ─────────────────────────────────────────────────────────
from admin import admin_router
app.include_router(admin_router)

# ── Auth dependency ────────────────────────────────────────────────────────────
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    try:
        user_response = supabase.auth.get_user(credentials.credentials)
        if not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid or expired session")
        return user_response.user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

# ── Models ─────────────────────────────────────────────────────────────────────
class UserRegister(BaseModel):
    email:        EmailStr
    password:     str
    role:         str = Field(..., pattern="^(employer|employee)$")
    company_name: Optional[str] = None
    full_name:    Optional[str] = None
    phone:        Optional[str] = None

class UserLogin(BaseModel):
    email:    EmailStr
    password: str

class EmployeeProfileUpdate(BaseModel):
    full_name:    Optional[str]  = None
    phone:        Optional[str]  = None
    is_available: Optional[bool] = None
    skills:       Optional[List[str]] = None
    work_details: Optional[str]  = None

EmployerRegister = UserRegister
EmployerLogin    = UserLogin

class JobCreate(BaseModel):
    title:            str = Field(..., alias="job_title")
    openings:         int = Field(..., gt=0)
    job_city:         str
    total_experience: str
    salary_min:       float
    salary_max:       float
    offers_bonus:     bool = False
    required_skills:  List[str] = []
    company_name:     str
    contact_person:   str
    phone_number:     str
    email:            EmailStr
    hiring_speed:     str
    hiring_frequency: str
    lat:              Optional[float] = None
    lng:              Optional[float] = None

    class Config:
        populate_by_name = True

class JobApply(BaseModel):
    full_name:  str
    email:      EmailStr
    phone:      str
    cover_note: Optional[str] = None

# ══════════════════════════════════════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/register")
async def register_user(user: UserRegister):
    if user.role == "employer" and not user.company_name:
        raise HTTPException(status_code=422, detail="company_name is required for employers.")
    try:
        auth_res = supabase.auth.sign_up({"email": user.email, "password": user.password})
        if not auth_res.user: raise HTTPException(status_code=400, detail="Registration failed.")
        user_id = auth_res.user.id
        if user.role == "employer":
            supabase.table("employers").upsert({"id": user_id, "company_name": user.company_name, "email": user.email}).execute()
        else:
            supabase.table("employees").upsert({"id": user_id, "email": user.email, "full_name": user.full_name, "phone": user.phone}).execute()
        return {"message": "Success", "user_id": user_id, "role": user.role}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/login")
async def login_user(credentials: UserLogin):
    try:
        res = supabase.auth.sign_in_with_password({"email": credentials.email, "password": credentials.password})
        return {"access_token": res.session.access_token, "user_id": res.user.id}
    except:
        raise HTTPException(status_code=401, detail="Invalid credentials.")

# ══════════════════════════════════════════════════════════════════════════════
# EMPLOYEE PROFILE MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/my-profile")
async def get_my_profile(current_user=Depends(get_current_user)):
    res = supabase.table("employees").select("*").eq("id", current_user.id).single().execute()
    return {"status": "success", "profile": res.data}

@app.patch("/my-profile")
async def update_my_profile(body: EmployeeProfileUpdate, current_user=Depends(get_current_user)):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates: raise HTTPException(status_code=422, detail="No fields provided.")
    res = supabase.table("employees").update(updates).eq("id", current_user.id).execute()
    return {"status": "success", "updated": res.data[0]}

# ══════════════════════════════════════════════════════════════════════════════
# JOBS — READ (Public)
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/jobs/search")
async def search_jobs(title: Optional[str] = None, city: Optional[str] = None):
    q = supabase.table("jobs").select("*").order("created_at", desc=True)
    if title: q = q.ilike("title", f"%{title}%")
    if city: q = q.ilike("job_city", f"%{city}%")
    return {"status": "success", "jobs": q.execute().data}

# ══════════════════════════════════════════════════════════════════════════════
# APPLICATIONS (Requires Auth)
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/jobs/{job_id}/apply", status_code=201)
async def apply_to_job(job_id: str, application: JobApply, current_user=Depends(get_current_user)):
    """Authenticated application submission."""
    data = {"job_id": job_id, **application.model_dump(), "employee_id": current_user.id}
    res = supabase.table("job_applications").insert(data).execute()
    return {"status": "success", "message": "Application submitted."}

# ══════════════════════════════════════════════════════════════════════════════
# JOB MANAGEMENT (Authenticated)
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/jobs", status_code=201)
async def post_job(job: JobCreate, current_user=Depends(get_current_user)):
    target_lat, target_lng = None, None
    if job.job_city:
        geo = gmaps.geocode(job.job_city)
        if geo:
            loc = geo[0]["geometry"]["location"]
            target_lat, target_lng = loc["lat"], loc["lng"]
    
    job_data = _build_job_data(job, current_user.id, target_lat, target_lng)
    res = supabase.table("jobs").insert(job_data).execute()
    return {"status": "success", "job_id": res.data[0].get("id")}

# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _build_job_data(job: JobCreate, employer_id: str, lat, lng) -> dict:
    data = {
        "employer_id": employer_id, "title": job.title, "openings": job.openings,
        "job_city": job.job_city, "total_experience": job.total_experience,
        "salary_min": job.salary_min, "salary_max": job.salary_max,
        "required_skills": job.required_skills, "company_name": job.company_name,
        "contact_person": job.contact_person, "phone_number": job.phone_number,
        "email": job.email, "hiring_speed": job.hiring_speed, "hiring_frequency": job.hiring_frequency
    }
    if lat: data.update({"lat": lat, "lng": lng})
    return data

@app.get("/health")
async def health():
    return {"status": "ok", "service": "LaborGrow API"}