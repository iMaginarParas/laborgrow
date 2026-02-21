import os
from typing import Optional, List
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
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

app = FastAPI(title="LaborGrow Professional Geo-Backend")

# --- CORS Fix for Professional Frontend ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Authentication Dependency ---
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        user_response = supabase.auth.get_user(credentials.credentials)
        if not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid or expired session")
        return user_response.user
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

# --- Pydantic Data Models ---
class EmployerRegister(BaseModel):
    email: EmailStr
    password: str
    company_name: str

class EmployerLogin(BaseModel):
    email: EmailStr
    password: str

class JobCreate(BaseModel):
    title: str = Field(..., alias="job_title") 
    openings: int = Field(..., gt=0)
    job_city: str 
    total_experience: str 
    salary_min: float
    salary_max: float
    offers_bonus: bool = False
    required_skills: List[str] = []
    company_name: str
    contact_person: str
    phone_number: str 
    email: EmailStr
    hiring_speed: str 
    hiring_frequency: str 
    lat: Optional[float] = None
    lng: Optional[float] = None

# --- API Endpoints ---

@app.post("/register")
async def register_employer(user: EmployerRegister):
    try:
        auth_response = supabase.auth.sign_up({"email": user.email, "password": user.password})
        if auth_response.user:
            supabase.table("employers").insert({
                "id": auth_response.user.id,
                "company_name": user.company_name,
                "email": user.email
            }).execute()
            return {"message": "Registration successful", "user_id": auth_response.user.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/login")
async def login_employer(credentials: EmployerLogin):
    try:
        response = supabase.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password
        })
        return {
            "access_token": response.session.access_token,
            "user_id": response.user.id
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/location/autocomplete")
async def get_suggestions(q: str = Query(..., min_length=2)):
    """Provides city suggestions as the employer types."""
    try:
        predictions = gmaps.places_autocomplete(input_text=q, types='(cities)')
        return predictions
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/jobs")
async def post_job(job: JobCreate, current_user = Depends(get_current_user)):
    """Main logic for saving jobs with geo-location processing."""
    target_lat = job.lat
    target_lng = job.lng

    if job.job_city and (target_lat is None or target_lng is None):
        try:
            geocode_result = gmaps.geocode(job.job_city)
            if geocode_result:
                loc = geocode_result[0]['geometry']['location']
                target_lat = loc['lat']
                target_lng = loc['lng']
        except Exception as e:
            print(f"Geocoding failed: {e}")

    try:
        # Prepare PostGIS-friendly point for Supabase
        point_str = f"POINT({target_lng} {target_lat})" if target_lng and target_lat else None
        
        job_data = {
            "employer_id": current_user.id,
            "title": job.title,
            "openings": job.openings,
            "job_city": job.job_city,
            "total_experience": job.total_experience,
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "offers_bonus": job.offers_bonus,
            "required_skills": job.required_skills,
            "company_name": job.company_name,
            "contact_person": job.contact_person,
            "phone_number": job.phone_number,
            "contact_email": job.email,
            "hiring_speed": job.hiring_speed,
            "hiring_frequency": job.hiring_frequency,
            "lat_long": point_str 
        }
        
        response = supabase.table("jobs").insert(job_data).execute()
        return {"status": "success", "job_id": response.data[0].get("id") if response.data else None}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Database Insertion Error: {str(e)}")

# --- New Geospatial Endpoint ---

@app.get("/jobs/nearby")
async def get_nearby_jobs(
    lat: float = Query(..., description="User's current latitude"),
    lng: float = Query(..., description="User's current longitude"),
    radius: float = Query(50000.0, description="Search radius in meters (default 50km)")
):
    """
    Calls the PostGIS 'get_jobs_nearby' function in Supabase to find nearby jobs.
    """
    try:
        # Executes the RPC function defined in your SQL Editor
        response = supabase.rpc("get_jobs_nearby", {
            "user_lat": lat,
            "user_lng": lng,
            "radius_meters": radius
        }).execute()

        return {
            "status": "success", 
            "results_count": len(response.data) if response.data else 0,
            "jobs": response.data if response.data else []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Nearby search failed: {str(e)}")