import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, EmailStr
from supabase import create_client, Client
import googlemaps

load_dotenv()

# --- Configuration ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY") # Ensure this is in your Railway variables

# Initialize Clients
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

app = FastAPI(title="LaborGrow Geo-API")

# --- Schemas ---
class EmployerRegister(BaseModel):
    email: EmailStr
    password: str
    company_name: str

class JobCreate(BaseModel):
    title: str
    description: str
    employer_id: str
    location_name: str = None  # Friendly name like "Mumbai, MH"
    lat: float = None           # Latitude from pin drop or GPS
    lng: float = None           # Longitude from pin drop or GPS

# --- Endpoints ---

@app.get("/location/autocomplete")
async def get_suggestions(q: str = Query(..., min_length=2)):
    """
    Feature 3: Returns location recommendations as the user types.
    """
    try:
        # Get predictions from Google Places
        predictions = gmaps.places_autocomplete(
            input_text=q,
            types='geocode' # Suggests addresses/cities
        )
        return predictions
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/jobs")
async def post_job(job: JobCreate):
    """
    Handles all 3 location types: Current Location, Pin Drop, and Search.
    """
    target_lat = job.lat
    target_lng = job.lng

    # If user selected a recommendation by name but we don't have coords yet:
    if job.location_name and (target_lat is None or target_lng is None):
        geocode_result = gmaps.geocode(job.location_name)
        if not geocode_result:
            raise HTTPException(status_code=400, detail="Invalid location name")
        
        loc = geocode_result[0]['geometry']['location']
        target_lat = loc['lat']
        target_lng = loc['lng']

    if target_lat is None or target_lng is None:
        raise HTTPException(status_code=400, detail="Coordinates are required to post a job")

    try:
        # POINT(longitude latitude) for PostGIS
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