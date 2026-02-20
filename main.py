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
    try:
        user_response = supabase.auth.get_user(credentials.credentials)
        if not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return user_response.user
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

# --- Updated Schemas ---
class EmployerRegister(BaseModel):
    email: EmailStr
    password: str
    company_name: str

class EmployerLogin(BaseModel):
    email: EmailStr
    password: str

class JobCreate(BaseModel):
    # Basic Job Details
    title: str = Field(..., alias="job_title")
    openings: int = Field(..., gt=0)
    job_city: str
    
    # Candidate Requirements
    total_experience: str # e.g., "1-2 years"
    salary_min: float
    salary_max: float
    offers_bonus: bool = False
    required_skills: List[str] = []
    
    # Company/Contact Details
    company_name: str
    contact_person: str
    phone_number: str # With +91 logic handled in frontend or regex here
    email: EmailStr
    
    # Hiring Metrics
    hiring_speed: str # "How soon do you want to fill..."
    hiring_frequency: str # "Every Month", "Once in a few months", etc.
    
    # Location data for Geo-API
    lat: Optional[float] = None
    lng: Optional[float] = None

# --- Endpoints ---

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
            return {"message": "Employer registered", "id": auth_response.user.id}
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
            "message": "Login successful",
            "access_token": response.session.access_token,
            "user_id": response.user.id
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid email or password")

@app.get("/location/autocomplete")
async def get_suggestions(q: str = Query(..., min_length=2)):
    try:
        predictions = gmaps.places_autocomplete(input_text=q, types='(cities)')
        return predictions
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/jobs")
async def post_job(job: JobCreate, current_user = Depends(get_current_user)):
    """Inserts job into Supabase with all form fields and Geo-coordinates."""
    
    target_lat = job.lat
    target_lng = job.lng

    # Geocode the city if coordinates weren't provided by the frontend map picker
    if job.job_city and (target_lat is None or target_lng is None):
        geocode_result = gmaps.geocode(job.job_city)
        if geocode_result:
            loc = geocode_result[0]['geometry']['location']
            target_lat = loc['lat']
            target_lng = loc['lng']

    try:
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
        return {"message": "Job posted successfully", "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Database Error: {str(e)}")