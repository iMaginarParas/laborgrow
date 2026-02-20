import os
from typing import Optional, List
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from supabase import create_client, Client
import googlemaps

load_dotenv()

# --- Configuration ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")

# Initialize Clients
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
security = HTTPBearer()

app = FastAPI(title="LaborGrow Geo-API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Auth Dependency ---
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verifies the Supabase JWT and returns user data."""
    try:
        # Verify token with Supabase Auth
        user_response = supabase.auth.get_user(credentials.credentials)
        if not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return user_response.user
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

# --- Schemas ---
class EmployerRegister(BaseModel):
    email: EmailStr
    password: str
    company_name: str

class EmployerLogin(BaseModel):
    email: EmailStr
    password: str

class JobCreate(BaseModel):
    title: str
    description: str
    # New Standard Job Fields
    employment_type: str  # Full-time, Part-time, Contract
    salary_range: Optional[str] = None
    experience_level: Optional[str] = None # Entry, Mid, Senior
    required_skills: List[str] = []
    remote_option: bool = False
    # Location data
    location_name: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None

# --- Endpoints ---

@app.post("/register")
async def register_employer(user: EmployerRegister):
    """Registers a new employer."""
    try:
        auth_response = supabase.auth.sign_up({"email": user.email, "password": user.password})
        if auth_response.user:
            supabase.table("employers").insert({
                "id": auth_response.user.id,
                "company_name": user.company_name,
                "email": user.email
            }).execute()
            return {"message": "Employer registered", "id": auth_response.user.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/login")
async def login_employer(credentials: EmployerLogin):
    """Authenticates employer and returns a JWT session."""
    try:
        response = supabase.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password
        })
        return {
            "message": "Login successful",
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "user_id": response.user.id
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

@app.get("/location/autocomplete")
async def get_suggestions(q: str = Query(..., min_length=2)):
    """Returns location recommendations as the user types."""
    try:
        predictions = gmaps.places_autocomplete(input_text=q, types='geocode')
        return predictions
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/jobs")
async def post_job(job: JobCreate, current_user = Depends(get_current_user)):
    """Inserts job into Supabase linked to the authenticated user."""
    target_lat = job.lat
    target_lng = job.lng

    if job.location_name and (target_lat is None or target_lng is None):
        geocode_result = gmaps.geocode(job.location_name)
        if not geocode_result:
            raise HTTPException(status_code=400, detail="Invalid location name")
        
        loc = geocode_result[0]['geometry']['location']
        target_lat = loc['lat']
        target_lng = loc['lng']

    if target_lat is None or target_lng is None:
        raise HTTPException(status_code=400, detail="Coordinates required")

    try:
        point_str = f"POINT({target_lng} {target_lat})"
        job_data = {
            "title": job.title,
            "description": job.description,
            "employer_id": current_user.id, # Automatically uses authenticated ID
            "employment_type": job.employment_type,
            "salary_range": job.salary_range,
            "experience_level": job.experience_level,
            "required_skills": job.required_skills,
            "remote_option": job.remote_option,
            "location_name": job.location_name or "Custom Pin",
            "lat_long": point_str
        }
        
        response = supabase.table("jobs").insert(job_data).execute()
        return {"message": "Job posted successfully", "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))