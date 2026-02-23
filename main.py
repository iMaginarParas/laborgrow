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

app = FastAPI(title="LaborGrow API", version="2.0.0")

# ── CORS ───────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        populate_by_name = True   # accepts both "job_title" (alias) and "title"


# ══════════════════════════════════════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/register")
async def register_employer(user: EmployerRegister):
    """
    Register a new employer account.

    FIXED vs v1:
    - Returns access_token so the frontend (S.token = data.access_token)
      has a valid token right after registration — without this, job
      posting always failed with "You must be logged in" after register.
    - Uses upsert on employers table so duplicate calls don't crash.
    """
    try:
        auth_res = supabase.auth.sign_up({
            "email":    user.email,
            "password": user.password,
        })

        if not auth_res.user:
            raise HTTPException(status_code=400, detail="Registration failed — no user returned.")

        user_id = auth_res.user.id

        supabase.table("employers").upsert({
            "id":           user_id,
            "company_name": user.company_name,
            "email":        user.email,
        }).execute()

        # If Supabase issued a session immediately (email confirm OFF) use it,
        # otherwise do an auto sign-in to get a token.
        access_token = None
        if auth_res.session:
            access_token = auth_res.session.access_token
        else:
            try:
                login_res = supabase.auth.sign_in_with_password({
                    "email":    user.email,
                    "password": user.password,
                })
                if login_res.session:
                    access_token = login_res.session.access_token
            except Exception:
                pass   # user can log in manually if this fails

        return {
            "message":      "Registration successful",
            "user_id":      user_id,
            "access_token": access_token,   # frontend reads data.access_token
        }

    except HTTPException:
        raise
    except Exception as e:
        msg = str(e)
        if "already registered" in msg.lower() or "already exists" in msg.lower():
            raise HTTPException(
                status_code=409,
                detail="An account with this email already exists. Please log in instead.",
            )
        raise HTTPException(status_code=400, detail=f"Registration error: {msg}")


@app.post("/login")
async def login_employer(credentials: EmployerLogin):
    """Sign in and return an access_token."""
    try:
        res = supabase.auth.sign_in_with_password({
            "email":    credentials.email,
            "password": credentials.password,
        })
        if not res.session:
            raise HTTPException(status_code=401, detail="Invalid email or password.")
        return {"access_token": res.session.access_token, "user_id": res.user.id}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid email or password.")


# ══════════════════════════════════════════════════════════════════════════════
# LOCATION
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/location/autocomplete")
async def location_autocomplete(q: str = Query(..., min_length=2)):
    """
    Google Places city autocomplete.
    Returns a list of prediction objects — frontend reads p.description from each.
    Used by:
      - Employer job post form (city field)
      - Landing page hero search bar (city field, NEW)
    """
    try:
        predictions = gmaps.places_autocomplete(input_text=q, types="(cities)")
        return predictions
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ══════════════════════════════════════════════════════════════════════════════
# JOBS — READ
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/jobs/search")
async def search_jobs(
    title:  Optional[str] = Query(None, description="Job title keyword"),
    city:   Optional[str] = Query(None, description="City name"),
    limit:  int           = Query(20, ge=1, le=100),
    offset: int           = Query(0, ge=0),
):
    """
    NEW — powers the landing page two-field search bar.

    GET /jobs/search?title=electrician&city=Mumbai

    Both params are optional and case-insensitive partial matches.
    Returns jobs ordered newest-first in the same shape as /jobs/nearby
    so the same frontend renderJobs() function works for both.
    """
    try:
        q = (
            supabase.table("jobs")
            .select(
                "id, title, company_name, job_city, total_experience, "
                "salary_min, salary_max, offers_bonus, openings, "
                "required_skills, hiring_speed, created_at"
            )
            .order("created_at", desc=True)
        )

        if title and title.strip():
            q = q.ilike("title", f"%{title.strip()}%")

        if city and city.strip():
            q = q.ilike("job_city", f"%{city.strip()}%")

        result = q.range(offset, offset + limit - 1).execute()
        jobs   = result.data or []

        return {
            "status": "success",
            "count":  len(jobs),
            "query":  {"title": title, "city": city},
            "jobs":   jobs,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/jobs/nearby")
async def get_nearby_jobs(
    lat:    float         = Query(..., description="User latitude"),
    lng:    float         = Query(..., description="User longitude"),
    radius: float         = Query(50000.0, description="Radius in metres (default 50 km)"),
    title:  Optional[str] = Query(None,    description="Optional job title keyword filter"),
):
    """
    Geospatial search via PostGIS RPC.

    UPDATED vs v1: now accepts optional ?title= so the landing page can
    filter by title + location in one call.

    Three-level fallback:
      1. RPC with title_filter param  (updated SQL function)
      2. RPC without title_filter     (old SQL function) + Python filter
      3. Plain table query            (no PostGIS / no RPC at all)

    Updated SQL to run in Supabase SQL Editor:

        CREATE OR REPLACE FUNCTION get_jobs_nearby(
            user_lat      float,
            user_lng      float,
            radius_meters float DEFAULT 50000,
            title_filter  text  DEFAULT NULL
        )
        RETURNS TABLE (
            id               uuid,
            title            text,
            company_name     text,
            job_city         text,
            total_experience text,
            salary_min       float,
            salary_max       float,
            offers_bonus     boolean,
            openings         int,
            required_skills  text[],
            hiring_speed     text,
            distance_meters  float
        )
        LANGUAGE sql AS $$
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
              AND (title_filter IS NULL OR title ILIKE ('%' || title_filter || '%'))
            ORDER BY distance_meters ASC;
        $$;
    """
    rpc_params: dict = {
        "user_lat":      lat,
        "user_lng":      lng,
        "radius_meters": radius,
    }
    if title:
        rpc_params["title_filter"] = title.strip()

    # Level 1: RPC with title_filter
    try:
        res  = supabase.rpc("get_jobs_nearby", rpc_params).execute()
        jobs = res.data or []
        return {"status": "success", "results_count": len(jobs), "jobs": jobs}
    except Exception as e:
        print(f"[nearby] level-1 error: {e}")

    # Level 2: RPC without title_filter (old SQL), filter in Python
    if title:
        try:
            res  = supabase.rpc("get_jobs_nearby", {
                "user_lat": lat, "user_lng": lng, "radius_meters": radius
            }).execute()
            jobs = [j for j in (res.data or [])
                    if title.lower() in (j.get("title") or "").lower()]
            return {"status": "success", "results_count": len(jobs), "jobs": jobs}
        except Exception as e:
            print(f"[nearby] level-2 error: {e}")

    # Level 3: Plain table query (no PostGIS)
    try:
        print("[nearby] RPC unavailable — plain table fallback")
        q = (
            supabase.table("jobs")
            .select(
                "id, title, company_name, job_city, total_experience, "
                "salary_min, salary_max, offers_bonus, openings, "
                "required_skills, hiring_speed"
            )
        )
        if title:
            q = q.ilike("title", f"%{title.strip()}%")

        fb = q.limit(20).execute()
        return {
            "status":        "success",
            "results_count": len(fb.data or []),
            "jobs":          fb.data or [],
            "warning":       (
                "get_jobs_nearby RPC not found — showing results without "
                "distance sort. See /jobs/nearby docstring to create it."
            ),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"All fallbacks failed: {str(e)}")


@app.get("/jobs")
async def list_jobs(
    limit:  int           = Query(20, ge=1, le=100),
    offset: int           = Query(0, ge=0),
    city:   Optional[str] = Query(None, description="Filter by city"),
):
    """
    NEW — paginated list of all jobs, newest first.
    Powers the landing page "Browse all jobs →" link.
    """
    try:
        q = (
            supabase.table("jobs")
            .select(
                "id, title, company_name, job_city, total_experience, "
                "salary_min, salary_max, offers_bonus, openings, "
                "required_skills, hiring_speed, created_at"
            )
            .order("created_at", desc=True)
        )
        if city:
            q = q.ilike("job_city", f"%{city}%")

        result = q.range(offset, offset + limit - 1).execute()
        jobs   = result.data or []
        return {"status": "success", "count": len(jobs), "jobs": jobs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch jobs: {str(e)}")


@app.get("/jobs/{job_id}")
async def get_job(job_id: str):
    """
    NEW — fetch a single job by its UUID.
    Used when a candidate clicks a job card to view full details.
    """
    try:
        result = (
            supabase.table("jobs")
            .select("*")
            .eq("id", job_id)
            .single()
            .execute()
        )
        if not result.data:
            raise HTTPException(status_code=404, detail="Job not found.")
        return result.data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ══════════════════════════════════════════════════════════════════════════════
# JOBS — WRITE
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/jobs", status_code=201)
async def post_job(job: JobCreate, current_user=Depends(get_current_user)):
    """
    Create a job posting (requires Bearer token from /login or /register).

    Accepts the exact payload the frontend sends:
        job_title, openings, job_city, total_experience,
        salary_min, salary_max, offers_bonus, required_skills,
        company_name, contact_person, phone_number, email,
        hiring_speed, hiring_frequency

    Geocodes job_city → lat/lng via Google Maps automatically.
    Strips unknown columns and retries up to 15 times — works regardless
    of your exact Supabase table schema.
    """
    target_lat = job.lat
    target_lng = job.lng

    if job.job_city and (target_lat is None or target_lng is None):
        try:
            geo = gmaps.geocode(job.job_city)
            if geo:
                loc        = geo[0]["geometry"]["location"]
                target_lat = loc["lat"]
                target_lng = loc["lng"]
                print(f"Geocoded '{job.job_city}' → {target_lat}, {target_lng}")
        except Exception as e:
            print(f"Geocoding failed: {e}")

    job_data   = _build_job_data(job, current_user.id, target_lat, target_lng)
    last_error = None

    for attempt in range(15):
        try:
            print(f"Insert attempt {attempt + 1} | cols: {list(job_data.keys())}")
            res = supabase.table("jobs").insert(job_data).execute()

            if res.data:
                job_id = res.data[0].get("id")
                print(f"✅ Job inserted — id={job_id}")
                return {"status": "success", "job_id": job_id, "attempts": attempt + 1}

            raise HTTPException(status_code=500, detail="Insert returned no data.")

        except HTTPException:
            raise
        except Exception as e:
            err        = str(e)
            last_error = err
            print(f"DB error (attempt {attempt + 1}): {err}")

            if "PGRST204" in err or "Could not find the" in err:
                job_data = _strip_unknown_column(job_data, err)
                if not job_data:
                    raise HTTPException(
                        status_code=500,
                        detail="All columns stripped — check jobs table schema."
                    )
                continue

            raise HTTPException(status_code=400, detail=f"Database error: {err}")

    raise HTTPException(
        status_code=400,
        detail=f"Insert failed after 15 attempts. Last error: {last_error}",
    )


# ══════════════════════════════════════════════════════════════════════════════
# DEBUG / HEALTH
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/schema/jobs")
async def jobs_schema():
    """Debug: returns columns present in the jobs table."""
    try:
        result = (
            supabase
            .from_("information_schema.columns")
            .select("column_name, data_type, is_nullable")
            .eq("table_name",   "jobs")
            .eq("table_schema", "public")
            .execute()
        )
        return {"columns": result.data}
    except Exception as e:
        return {
            "error": str(e),
            "tip":   "Run: SELECT column_name FROM information_schema.columns "
                     "WHERE table_name='jobs' in your Supabase SQL editor.",
        }


@app.get("/health")
async def health():
    return {"status": "ok", "service": "LaborGrow API", "version": "2.0.0"}


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _build_job_data(job: JobCreate, employer_id: str, lat, lng) -> dict:
    """
    Build the maximal column dict. Unknown columns are stripped one-by-one
    on retries until the insert succeeds.
    """
    data: dict = {
        "employer_id":      employer_id,
        "title":            job.title,
        "openings":         job.openings,
        "job_city":         job.job_city,
        "total_experience": job.total_experience,
        "salary_min":       job.salary_min,
        "salary_max":       job.salary_max,
        "offers_bonus":     job.offers_bonus,
        "required_skills":  job.required_skills,
        "company_name":     job.company_name,
        "contact_person":   job.contact_person,
        "phone_number":     job.phone_number,
        "contact_email":    job.email,
        "email":            job.email,
        "hiring_speed":     job.hiring_speed,
        "hiring_frequency": job.hiring_frequency,
    }
    if lat is not None and lng is not None:
        wkt               = f"SRID=4326;POINT({lng} {lat})"
        data["lat_long"]  = wkt
        data["lat"]       = lat
        data["lng"]       = lng
        data["latitude"]  = lat
        data["longitude"] = lng
        data["location"]  = wkt
    return data


def _strip_unknown_column(data: dict, error_msg: str) -> dict:
    """Remove the column named in a PGRST204 error and return the slimmed dict."""
    m = re.search(r"Could not find the '(\w+)' column", error_msg)
    if m:
        bad = m.group(1)
        print(f"  → Stripping unknown column '{bad}'")
        return {k: v for k, v in data.items() if k != bad}
    return data