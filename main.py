import os
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from supabase import create_client, Client

# --- Configuration ---
SUPABASE_URL         = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise ValueError("Supabase environment variables are missing.")

supabase: Client     = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
security             = HTTPBearer()

app = FastAPI(title="WorkerFinder API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---
class AuthRequest(BaseModel):
    email: EmailStr
    password: str

class WorkerProfileUpdate(BaseModel):
    full_name:    Optional[str]  = None
    city:         Optional[str]  = None
    is_available: Optional[bool] = None
    skills:       Optional[List[str]] = None
    lat:          Optional[float] = None
    lng:          Optional[float] = None

class JobCreate(BaseModel):
    title: str
    description: str
    location: str
    budget: Optional[float] = None

# --- Auth Dependency ---
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        user_res = supabase.auth.get_user(credentials.credentials)
        if not user_res.user: 
            raise Exception("No user found")
        return user_res.user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

# --- AUTHENTICATION ROUTES ---
@app.post("/auth/register")
async def register(body: AuthRequest):
    try:
        res = supabase.auth.sign_up({"email": body.email, "password": body.password})
        return {"status": "success", "user": res.user}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/login")
async def login(body: AuthRequest):
    try:
        res = supabase.auth.sign_in_with_password({"email": body.email, "password": body.password})
        return {"status": "success", "session": res.session}
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

# --- PUBLIC ROUTES ---
@app.get("/workers/search")
async def search_workers(city: Optional[str] = None, skill: Optional[str] = None):
    query = supabase.table("employees").select("id, full_name, city, skills").eq("is_available", True)
    if city: query = query.ilike("city", f"%{city}%")
    if skill: query = query.contains("skills", [skill])
    res = query.execute()
    return {"status": "success", "data": res.data}

@app.get("/workers/{worker_id}")
async def get_worker_public(worker_id: str):
    try:
        res = supabase.table("employees").select("full_name, city, skills").eq("id", worker_id).single().execute()
        return {"worker": res.data}
    except Exception:
        raise HTTPException(status_code=404, detail="Worker not found")

@app.get("/jobs/search")
async def search_jobs(location: Optional[str] = None, title: Optional[str] = None):
    # Fixed: Changed 'created_by' to 'employer_id' in the select string
    query = supabase.table("jobs").select("id, title, location, budget, employer_id")
    if location: query = query.ilike("location", f"%{location}%")
    if title: query = query.ilike("title", f"%{title}%")
    res = query.execute()
    return {"status": "success", "data": res.data}

# --- PRIVATE ROUTES (Requires Auth) ---
@app.post("/my-profile")
async def upsert_profile(body: WorkerProfileUpdate, current_user=Depends(get_current_user)):
    data = body.model_dump(exclude_none=True)
    data["id"] = current_user.id 
    data["email"] = current_user.email 
    try:
        res = supabase.table("employees").upsert(data).execute()
        return {"status": "success", "data": res.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/jobs")
async def create_job(body: JobCreate, current_user=Depends(get_current_user)):
    job_data = body.model_dump()
    # Fixed: Changed the dictionary key to match the database column
    job_data["employer_id"] = current_user.id
    try:
        res = supabase.table("jobs").insert(job_data).execute()
        return {"status": "success", "data": res.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/health")
async def health():
    return {"status": "online"}