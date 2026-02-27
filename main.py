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

# Service-role client — bypasses ALL Supabase RLS policies.
# All ownership/auth checks are done in Python, not Postgres RLS.
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
        raise HTTPException(
            status_code=422,
            detail="company_name is required when role is 'employer'.",
        )

    try:
        auth_res = supabase.auth.sign_up({
            "email":    user.email,
            "password": user.password,
        })

        if not auth_res.user:
            raise HTTPException(status_code=400, detail="Registration failed — no user returned.")

        user_id = auth_res.user.id

        if user.role == "employer":
            supabase.table("employers").upsert({
                "id":           user_id,
                "company_name": user.company_name,
                "email":        user.email,
            }).execute()
        else:
            profile: dict = {"id": user_id, "email": user.email}
            if user.full_name:
                profile["full_name"] = user.full_name
            if user.phone:
                profile["phone"] = user.phone
            supabase.table("employees").upsert(profile).execute()

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
                pass

        return {
            "message":      "Registration successful",
            "user_id":      user_id,
            "role":         user.role,
            "access_token": access_token,
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
async def login_user(credentials: UserLogin):
    try:
        res = supabase.auth.sign_in_with_password({
            "email":    credentials.email,
            "password": credentials.password,
        })
        if not res.session:
            raise HTTPException(status_code=401, detail="Invalid email or password.")

        user_id = res.user.id

        role = "employee"
        try:
            emp = (
                supabase.table("employers")
                .select("id")
                .eq("id", user_id)
                .maybe_single()
                .execute()
            )
            if emp.data:
                role = "employer"
        except Exception:
            pass

        return {
            "access_token": res.session.access_token,
            "user_id":      user_id,
            "role":         role,
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid email or password.")


# ══════════════════════════════════════════════════════════════════════════════
# LOCATION
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/location/autocomplete")
async def location_autocomplete(q: str = Query(..., min_length=2)):
    """Google Places city autocomplete."""
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
    title:  Optional[str] = Query(None),
    city:   Optional[str] = Query(None),
    limit:  int           = Query(20, ge=1, le=100),
    offset: int           = Query(0, ge=0),
):
    """Powers the landing page search bar. Public — no auth required."""
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
        return {"status": "success", "count": len(jobs), "query": {"title": title, "city": city}, "jobs": jobs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/jobs/nearby")
async def get_nearby_jobs(
    lat:    float         = Query(...),
    lng:    float         = Query(...),
    radius: float         = Query(50000.0),
    title:  Optional[str] = Query(None),
):
    """Geospatial job search via PostGIS RPC with Python fallbacks."""
    rpc_params: dict = {"user_lat": lat, "user_lng": lng, "radius_meters": radius}
    if title:
        rpc_params["title_filter"] = title.strip()

    try:
        res  = supabase.rpc("get_jobs_nearby", rpc_params).execute()
        jobs = res.data or []
        return {"status": "success", "results_count": len(jobs), "jobs": jobs}
    except Exception as e:
        print(f"[nearby] level-1 error: {e}")

    if title:
        try:
            res  = supabase.rpc("get_jobs_nearby", {"user_lat": lat, "user_lng": lng, "radius_meters": radius}).execute()
            jobs = [j for j in (res.data or []) if title.lower() in (j.get("title") or "").lower()]
            return {"status": "success", "results_count": len(jobs), "jobs": jobs}
        except Exception as e:
            print(f"[nearby] level-2 error: {e}")

    try:
        q = supabase.table("jobs").select(
            "id, title, company_name, job_city, total_experience, "
            "salary_min, salary_max, offers_bonus, openings, required_skills, hiring_speed"
        )
        if title:
            q = q.ilike("title", f"%{title.strip()}%")
        fb = q.limit(20).execute()
        return {
            "status":       "success",
            "results_count": len(fb.data or []),
            "jobs":          fb.data or [],
            "warning":       "PostGIS RPC unavailable — showing results without distance sort.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"All fallbacks failed: {str(e)}")


@app.get("/jobs")
async def list_jobs(
    limit:  int           = Query(20, ge=1, le=100),
    offset: int           = Query(0, ge=0),
    city:   Optional[str] = Query(None),
):
    """
    Public paginated job list, newest first.
    Includes employer_id so the frontend can filter My Jobs client-side.
    """
    try:
        q = (
            supabase.table("jobs")
            .select(
                "id, employer_id, title, company_name, job_city, total_experience, "
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


# ══════════════════════════════════════════════════════════════════════════════
# MY JOBS — authenticated employer's own postings
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/my-jobs")
async def get_my_jobs(
    current_user=Depends(get_current_user),
    limit:  int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """
    Returns ONLY the jobs posted by the authenticated employer.

    GET /my-jobs
    Authorization: Bearer <token>
    """
    try:
        result = (
            supabase.table("jobs")
            .select(
                "id, employer_id, title, company_name, job_city, total_experience, "
                "salary_min, salary_max, offers_bonus, openings, "
                "required_skills, hiring_speed, created_at"
            )
            .eq("employer_id", current_user.id)
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        jobs = result.data or []
        return {"status": "success", "count": len(jobs), "jobs": jobs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch your jobs: {str(e)}")


@app.get("/jobs/{job_id}")
async def get_job(job_id: str):
    """Fetch a single job by UUID."""
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
# APPLICATIONS
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/jobs/{job_id}/apply", status_code=201)
async def apply_to_job(job_id: str, application: JobApply):
    """
    Submit a job application. No login required.

    The supabase client uses the SERVICE ROLE key, which bypasses RLS entirely.
    If you want extra safety, run in Supabase SQL Editor:
        ALTER TABLE job_applications DISABLE ROW LEVEL SECURITY;
    Or add a permissive INSERT policy:
        CREATE POLICY "allow_all_inserts" ON job_applications
        FOR INSERT WITH CHECK (true);
    """
    # Verify job exists
    try:
        job_res = (
            supabase.table("jobs")
            .select("id, employer_id")
            .eq("id", job_id)
            .single()
            .execute()
        )
        if not job_res.data:
            raise HTTPException(status_code=404, detail="Job not found.")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=404, detail="Job not found.")

    # Prevent duplicate applications from same email
    try:
        dup = (
            supabase.table("job_applications")
            .select("id")
            .eq("job_id", job_id)
            .eq("email", application.email)
            .execute()
        )
        if dup.data:
            raise HTTPException(
                status_code=409,
                detail="You have already applied to this job with this email address.",
            )
    except HTTPException:
        raise
    except Exception:
        pass  # if duplicate check fails, still try the insert

    # Insert — service-role client bypasses RLS
    try:
        res = (
            supabase.table("job_applications")
            .insert({
                "job_id":     job_id,
                "full_name":  application.full_name,
                "email":      application.email,
                "phone":      application.phone,
                "cover_note": application.cover_note,
            })
            .execute()
        )
        if not res.data:
            raise HTTPException(status_code=500, detail="Application submission failed.")

        return {
            "status":         "success",
            "message":        "Application submitted successfully.",
            "application_id": res.data[0].get("id"),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit application: {str(e)}")


@app.get("/jobs/{job_id}/applicants")
async def get_job_applicants(job_id: str, current_user=Depends(get_current_user)):
    """
    Returns all applicants for a job.
    Only accessible by the employer who originally posted the job.
    """
    try:
        job_res = (
            supabase.table("jobs")
            .select("id, employer_id, title, company_name")
            .eq("id", job_id)
            .single()
            .execute()
        )
        if not job_res.data:
            raise HTTPException(status_code=404, detail="Job not found.")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=404, detail="Job not found.")

    job = job_res.data
    if job["employer_id"] != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Access denied — you can only view applicants for your own job postings.",
        )

    try:
        apps_res = (
            supabase.table("job_applications")
            .select("id, full_name, email, phone, cover_note, applied_at")
            .eq("job_id", job_id)
            .order("applied_at", desc=True)
            .execute()
        )
        applicants = apps_res.data or []

        return {
            "status":           "success",
            "job_id":           job_id,
            "job_title":        job["title"],
            "company_name":     job["company_name"],
            "total_applicants": len(applicants),
            "applicants":       applicants,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch applicants: {str(e)}")


@app.post("/jobs", status_code=201)
async def post_job(job: JobCreate, current_user=Depends(get_current_user)):
    """
    Create a job posting (requires Bearer token from /login or /register).
    Geocodes job_city → lat/lng via Google Maps.
    Strips unknown columns and retries up to 15 times.
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
    return {"status": "ok", "service": "LaborGrow API", "version": "2.3.0"}


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _build_job_data(job: JobCreate, employer_id: str, lat, lng) -> dict:
    """Build the maximal column dict. Unknown columns are stripped on retry."""
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