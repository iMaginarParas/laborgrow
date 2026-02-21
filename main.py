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

# --- CORS ---
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
    except HTTPException:
        raise
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

    class Config:
        populate_by_name = True  # allows both 'title' and 'job_title'


# ═══════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════

@app.post("/register")
async def register_employer(user: EmployerRegister):
    try:
        auth_response = supabase.auth.sign_up({
            "email": user.email,
            "password": user.password
        })

        if not auth_response.user:
            raise HTTPException(status_code=400, detail="Registration failed — no user returned.")

        user_id = auth_response.user.id

        # ── FIX 1: upsert instead of insert so duplicate registrations don't crash ──
        supabase.table("employers").upsert({
            "id": user_id,
            "company_name": user.company_name,
            "email": user.email
        }).execute()

        return {"message": "Registration successful", "user_id": user_id}

    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        # Supabase returns "User already registered" for duplicate emails
        if "already registered" in error_msg.lower() or "already exists" in error_msg.lower():
            raise HTTPException(
                status_code=409,
                detail="An account with this email already exists. Please log in instead."
            )
        raise HTTPException(status_code=400, detail=f"Registration error: {error_msg}")


@app.post("/login")
async def login_employer(credentials: EmployerLogin):
    try:
        response = supabase.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password
        })

        if not response.session:
            raise HTTPException(status_code=401, detail="Invalid email or password.")

        return {
            "access_token": response.session.access_token,
            "user_id": response.user.id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid email or password.")


@app.get("/location/autocomplete")
async def get_suggestions(q: str = Query(..., min_length=2)):
    """City autocomplete via Google Places."""
    try:
        predictions = gmaps.places_autocomplete(input_text=q, types='(cities)')
        return predictions
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/jobs")
async def post_job(job: JobCreate, current_user=Depends(get_current_user)):
    """Save a job posting with geo-location. Geocodes city if lat/lng not provided."""

    target_lat = job.lat
    target_lng = job.lng

    # ── Geocode the city if coordinates not already provided ──
    if job.job_city and (target_lat is None or target_lng is None):
        try:
            geocode_result = gmaps.geocode(job.job_city)
            if geocode_result:
                loc = geocode_result[0]['geometry']['location']
                target_lat = loc['lat']
                target_lng = loc['lng']
                print(f"Geocoded '{job.job_city}' → lat={target_lat}, lng={target_lng}")
            else:
                print(f"Geocoding returned no results for '{job.job_city}'")
        except Exception as e:
            print(f"Geocoding failed for '{job.job_city}': {e}")

    try:
        # ── FIX 2: Use ST_GeomFromText with SRID 4326 for PostGIS ──
        # Plain "POINT(lng lat)" string doesn't work with geography columns.
        # We pass lat/lng as plain floats and let Supabase/PostGIS handle it via RPC,
        # OR we use the correct WKT with SRID that PostGIS geography columns expect.
        # The safest approach: store lat/lng as separate float columns if geography fails,
        # OR call a Supabase RPC that does ST_GeomFromText internally.
        #
        # OPTION A — store as WKT text (works if lat_long is TEXT type):
        #   point_str = f"POINT({target_lng} {target_lat})"
        #
        # OPTION B — pass coords to an RPC that handles geometry internally.
        #
        # OPTION C (most compatible) — pass lat & lng as floats, let the DB function build geometry.
        # We use this approach below.

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
        }

        # ── FIX 2 (continued): Add geometry only if we have valid coords ──
        if target_lat is not None and target_lng is not None:
            # PostGIS geography column requires ST_GeomFromText — pass via RPC or use raw SQL
            # Most Supabase setups accept this WKT string for geography columns:
            job_data["lat_long"] = f"SRID=4326;POINT({target_lng} {target_lat})"
            # Also store raw floats as backup columns (if those columns exist in your table)
            job_data["lat"] = target_lat
            job_data["lng"] = target_lng

        response = supabase.table("jobs").insert(job_data).execute()

        if not response.data:
            raise HTTPException(status_code=500, detail="Insert returned no data.")

        return {
            "status": "success",
            "job_id": response.data[0].get("id")
        }

    except HTTPException:
        raise
    except Exception as e:
        error_detail = str(e)
        print(f"DB insert error: {error_detail}")

        # ── FIX 3: Retry without geometry if PostGIS column fails ──
        if "lat_long" in error_detail or "geometry" in error_detail or "geography" in error_detail:
            print("Retrying insert WITHOUT lat_long geometry column...")
            try:
                job_data_fallback = {k: v for k, v in job_data.items()
                                     if k not in ("lat_long", "lat", "lng")}
                response2 = supabase.table("jobs").insert(job_data_fallback).execute()
                if response2.data:
                    return {
                        "status": "success",
                        "job_id": response2.data[0].get("id"),
                        "warning": "Job saved without geo-coordinates. Check your lat_long column type."
                    }
            except Exception as e2:
                raise HTTPException(status_code=400, detail=f"Database error (fallback also failed): {str(e2)}")

        raise HTTPException(status_code=400, detail=f"Database Insertion Error: {error_detail}")


# ═══════════════════════════════════════════════════════
# GEOSPATIAL — Nearby Jobs
# ═══════════════════════════════════════════════════════

@app.get("/jobs/nearby")
async def get_nearby_jobs(
    lat: float = Query(..., description="User's latitude"),
    lng: float = Query(..., description="User's longitude"),
    radius: float = Query(50000.0, description="Search radius in meters (default 50km)")
):
    """
    Calls the PostGIS 'get_jobs_nearby' RPC function in Supabase.

    Required SQL in Supabase (run in SQL Editor if not already created):

        CREATE OR REPLACE FUNCTION get_jobs_nearby(
            user_lat float,
            user_lng float,
            radius_meters float DEFAULT 50000
        )
        RETURNS TABLE (
            id uuid,
            title text,
            company_name text,
            job_city text,
            total_experience text,
            salary_min float,
            salary_max float,
            offers_bonus boolean,
            openings int,
            required_skills text[],
            hiring_speed text,
            distance_meters float
        )
        LANGUAGE sql
        AS $$
            SELECT
                id, title, company_name, job_city, total_experience,
                salary_min, salary_max, offers_bonus, openings,
                required_skills, hiring_speed,
                ST_Distance(
                    lat_long::geography,
                    ST_SetSRID(ST_MakePoint(user_lng, user_lat), 4326)::geography
                ) AS distance_meters
            FROM jobs
            WHERE ST_DWithin(
                lat_long::geography,
                ST_SetSRID(ST_MakePoint(user_lng, user_lat), 4326)::geography,
                radius_meters
            )
            ORDER BY distance_meters ASC;
        $$;
    """
    try:
        response = supabase.rpc("get_jobs_nearby", {
            "user_lat": lat,
            "user_lng": lng,
            "radius_meters": radius
        }).execute()

        jobs = response.data if response.data else []

        return {
            "status": "success",
            "results_count": len(jobs),
            "jobs": jobs
        }

    except Exception as e:
        error_msg = str(e)
        print(f"Nearby search error: {error_msg}")

        # ── FIX 4: Fallback — if RPC doesn't exist, do a plain table query ──
        if "function" in error_msg.lower() or "rpc" in error_msg.lower() or "does not exist" in error_msg.lower():
            try:
                print("RPC not found — falling back to plain table query (no distance filtering)")
                fallback = supabase.table("jobs").select(
                    "id, title, company_name, job_city, total_experience, "
                    "salary_min, salary_max, offers_bonus, openings, required_skills, hiring_speed"
                ).limit(20).execute()

                return {
                    "status": "success",
                    "results_count": len(fallback.data or []),
                    "jobs": fallback.data or [],
                    "warning": "get_jobs_nearby RPC not found. Showing all jobs. See backend docs to create the SQL function."
                }
            except Exception as e2:
                raise HTTPException(status_code=500, detail=f"Fallback query also failed: {str(e2)}")

        raise HTTPException(status_code=500, detail=f"Nearby search failed: {error_msg}")