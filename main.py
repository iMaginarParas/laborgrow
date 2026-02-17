import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware # Required for browser security
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

app = FastAPI(title="LaborGrow Geo-API")

# --- CORS CONFIGURATION ---
# This allows your frontend (Live Server, Localhost, or Production URL) 
# to talk to this API without being blocked by the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, replace ["*"] with your actual frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    employer_id: str
    location_name: str = None
    lat: float = None
    lng: float = None

# --- Endpoints ---

@app.get("/location/autocomplete")
async def get_suggestions(q: str = Query(..., min_length=2)):
    """Returns location recommendations as the user types."""
    try:
        predictions = gmaps.places_autocomplete(
            input_text=q,
            types='geocode'
        )
        return predictions
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/jobs")
async def post_job(job: JobCreate):
    """Handles location logic and inserts job into Supabase."""
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
        response = supabase.table("jobs").insert({
            "title": job.title,
            "description": job.description,
            "employer_id": job.employer_id,
            "location_name": job.location_name or "Custom Pin",
            "lat_long": point_str
        }).execute()

        return {"message": "Job posted successfully", "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/register")
async def register_employer(user: EmployerRegister):
    """Registers a new employer and creates a profile record."""
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
    """Authenticates existing employers."""
    try:
        response = supabase.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password
        })
        return {
            "message": "Login successful", 
            "id": response.user.id,
            "email": response.user.email
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid credentials")