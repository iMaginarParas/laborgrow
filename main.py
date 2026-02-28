import os
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from supabase import create_client, Client

# Configuration
SUPABASE_URL         = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client     = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
security             = HTTPBearer()

app = FastAPI(title="WorkerFinder API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Models ---
class WorkerProfileUpdate(BaseModel):
    full_name:    Optional[str]  = None
    city:         Optional[str]  = None
    is_available: Optional[bool] = None
    skills:       Optional[List[str]] = None
    lat:          Optional[float] = None
    lng:          Optional[float] = None

# --- Auth Helper ---
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        user_res = supabase.auth.get_user(credentials.credentials)
        if not user_res.user: raise Exception
        return user_res.user
    except:
        raise HTTPException(status_code=401, detail="Invalid session")

# --- PUBLIC ROUTES ---
@app.get("/workers/search")
async def search_workers(city: Optional[str] = None, skill: Optional[str] = None):
    """Public search: No auth required. Only shows available workers."""
    query = supabase.table("employees").select("id, full_name, city, skills").eq("is_available", True)
    
    if city: query = query.ilike("city", f"%{city}%")
    if skill: query = query.contains("skills", [skill])
        
    return {"status": "success", "data": query.execute().data}

@app.get("/workers/{worker_id}")
async def get_worker_public(worker_id: str):
    """Public view: Basic info only."""
    res = supabase.table("employees").select("full_name, city, skills").eq("id", worker_id).single().execute()
    return {"worker": res.data}

# --- PRIVATE ROUTES (Requires Auth) ---
@app.patch("/my-profile")
async def update_profile(body: WorkerProfileUpdate, current_user=Depends(get_current_user)):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    res = supabase.table("employees").update(updates).eq("id", current_user.id).execute()
    return {"status": "success", "updated": res.data[0]}

@app.get("/health")
async def health():
    return {"status": "online"}