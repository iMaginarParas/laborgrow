"""
LaborGrow — Master Admin Panel
================================
Mounted automatically by main.py.

All admin routes are protected by the X-Admin-Key header.
Add to your .env:
    ADMIN_SECRET_KEY=your-super-secret-key-here

Example request:
    GET /admin/dashboard
    X-Admin-Key: your-super-secret-key-here
"""

import os
from typing import Optional
from fastapi import APIRouter, HTTPException, Header, Query, Depends
from pydantic import BaseModel, EmailStr
from supabase import create_client, Client

# ── Shared Supabase client (reuses service-role key from env) ─────────────────
SUPABASE_URL         = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
ADMIN_SECRET_KEY     = os.environ.get("ADMIN_SECRET_KEY", "change-me-in-env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

admin_router = APIRouter(prefix="/admin", tags=["Admin Panel"])


# ══════════════════════════════════════════════════════════════════════════════
# AUTH DEPENDENCY
# ══════════════════════════════════════════════════════════════════════════════

def require_admin(x_admin_key: str = Header(...)):
    """Validates X-Admin-Key header against ADMIN_SECRET_KEY in .env."""
    if x_admin_key != ADMIN_SECRET_KEY:
        raise HTTPException(status_code=403, detail="Invalid or missing admin key.")


# ══════════════════════════════════════════════════════════════════════════════
# MODELS
# ══════════════════════════════════════════════════════════════════════════════

class AdminJobUpdate(BaseModel):
    title:            Optional[str]   = None
    openings:         Optional[int]   = None
    job_city:         Optional[str]   = None
    total_experience: Optional[str]   = None
    salary_min:       Optional[float] = None
    salary_max:       Optional[float] = None
    offers_bonus:     Optional[bool]  = None
    hiring_speed:     Optional[str]   = None
    hiring_frequency: Optional[str]   = None

class AdminEmployerUpdate(BaseModel):
    company_name: Optional[str]      = None
    email:        Optional[EmailStr] = None

class AdminEmployeeUpdate(BaseModel):
    full_name: Optional[str]      = None
    email:     Optional[EmailStr] = None
    phone:     Optional[str]      = None


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

@admin_router.get("/dashboard", dependencies=[Depends(require_admin)])
async def admin_dashboard():
    """
    Single-call platform overview — total counts + recent activity.
    Use this as the first thing your admin panel loads.
    """
    try:
        total_jobs         = supabase.table("jobs").select("id", count="exact").execute()
        total_employers    = supabase.table("employers").select("id", count="exact").execute()
        total_employees    = supabase.table("employees").select("id", count="exact").execute()
        total_applications = supabase.table("job_applications").select("id", count="exact").execute()

        recent_jobs = (
            supabase.table("jobs")
            .select("id, title, company_name, job_city, created_at")
            .order("created_at", desc=True)
            .limit(5)
            .execute()
        )

        recent_apps = (
            supabase.table("job_applications")
            .select("id, full_name, email, job_id, applied_at")
            .order("applied_at", desc=True)
            .limit(5)
            .execute()
        )

        return {
            "status": "success",
            "stats": {
                "total_jobs":         total_jobs.count,
                "total_employers":    total_employers.count,
                "total_employees":    total_employees.count,
                "total_applications": total_applications.count,
            },
            "recent_jobs":         recent_jobs.data or [],
            "recent_applications": recent_apps.data or [],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dashboard error: {str(e)}")


# ══════════════════════════════════════════════════════════════════════════════
# EMPLOYER MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

@admin_router.get("/users/employers", dependencies=[Depends(require_admin)])
async def list_employers(
    limit:  int           = Query(20, ge=1, le=100),
    offset: int           = Query(0, ge=0),
    search: Optional[str] = Query(None, description="Search by company name"),
):
    """Paginated employer list with job count per employer."""
    try:
        q = supabase.table("employers").select("id, company_name, email, created_at")
        if search:
            q = q.ilike("company_name", f"%{search}%")

        result    = q.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
        employers = result.data or []

        for emp in employers:
            try:
                cnt            = supabase.table("jobs").select("id", count="exact").eq("employer_id", emp["id"]).execute()
                emp["job_count"] = cnt.count or 0
            except Exception:
                emp["job_count"] = None

        return {"status": "success", "count": len(employers), "employers": employers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.get("/users/employers/{employer_id}", dependencies=[Depends(require_admin)])
async def get_employer(employer_id: str):
    """Full employer profile + all their job postings."""
    try:
        emp_res = (
            supabase.table("employers")
            .select("id, company_name, email, created_at")
            .eq("id", employer_id)
            .single()
            .execute()
        )
        if not emp_res.data:
            raise HTTPException(status_code=404, detail="Employer not found.")

        jobs_res = (
            supabase.table("jobs")
            .select("id, title, job_city, openings, salary_min, salary_max, created_at")
            .eq("employer_id", employer_id)
            .order("created_at", desc=True)
            .execute()
        )

        return {
            "status":   "success",
            "employer": emp_res.data,
            "jobs":     jobs_res.data or [],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.patch("/users/employers/{employer_id}", dependencies=[Depends(require_admin)])
async def update_employer(employer_id: str, body: AdminEmployerUpdate):
    """Update an employer's profile fields."""
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=422, detail="No fields provided to update.")
    try:
        res = supabase.table("employers").update(updates).eq("id", employer_id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Employer not found.")
        return {"status": "success", "updated": res.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ══════════════════════════════════════════════════════════════════════════════
# EMPLOYEE MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

@admin_router.get("/users/employees", dependencies=[Depends(require_admin)])
async def list_employees(
    limit:  int           = Query(20, ge=1, le=100),
    offset: int           = Query(0, ge=0),
    search: Optional[str] = Query(None, description="Search by name or email"),
):
    """Paginated employee (job seeker) list."""
    try:
        q = supabase.table("employees").select("id, full_name, email, phone, created_at")
        if search:
            q = q.ilike("full_name", f"%{search}%")

        result = q.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
        return {"status": "success", "count": len(result.data or []), "employees": result.data or []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.get("/users/employees/{employee_id}", dependencies=[Depends(require_admin)])
async def get_employee(employee_id: str):
    """Full employee profile + their application history."""
    try:
        emp_res = (
            supabase.table("employees")
            .select("id, full_name, email, phone, created_at")
            .eq("id", employee_id)
            .single()
            .execute()
        )
        if not emp_res.data:
            raise HTTPException(status_code=404, detail="Employee not found.")

        apps_res = (
            supabase.table("job_applications")
            .select("id, job_id, full_name, email, phone, cover_note, applied_at")
            .eq("email", emp_res.data["email"])
            .order("applied_at", desc=True)
            .execute()
        )

        return {
            "status":       "success",
            "employee":     emp_res.data,
            "applications": apps_res.data or [],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.patch("/users/employees/{employee_id}", dependencies=[Depends(require_admin)])
async def update_employee(employee_id: str, body: AdminEmployeeUpdate):
    """Update an employee's profile fields."""
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=422, detail="No fields provided to update.")
    try:
        res = supabase.table("employees").update(updates).eq("id", employee_id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Employee not found.")
        return {"status": "success", "updated": res.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ══════════════════════════════════════════════════════════════════════════════
# DELETE USER (works for both employers and employees)
# ══════════════════════════════════════════════════════════════════════════════

@admin_router.delete("/users/{user_id}", dependencies=[Depends(require_admin)])
async def delete_user(user_id: str):
    """
    Permanently deletes a user from Supabase Auth + both profile tables.
    Also removes all jobs and applications tied to this user.
    USE WITH CAUTION — cannot be undone.
    """
    try:
        # Remove jobs posted by this user + their applications
        jobs_res = supabase.table("jobs").select("id").eq("employer_id", user_id).execute()
        for job in (jobs_res.data or []):
            supabase.table("job_applications").delete().eq("job_id", job["id"]).execute()
        supabase.table("jobs").delete().eq("employer_id", user_id).execute()

        # Remove profile rows
        supabase.table("employers").delete().eq("id", user_id).execute()
        supabase.table("employees").delete().eq("id", user_id).execute()

        # Delete from Supabase Auth
        supabase.auth.admin.delete_user(user_id)

        return {"status": "success", "message": f"User {user_id} and all associated data deleted."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")


# ══════════════════════════════════════════════════════════════════════════════
# JOB MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

@admin_router.get("/jobs", dependencies=[Depends(require_admin)])
async def admin_list_jobs(
    limit:       int           = Query(20, ge=1, le=100),
    offset:      int           = Query(0, ge=0),
    search:      Optional[str] = Query(None, description="Search by title or city"),
    employer_id: Optional[str] = Query(None, description="Filter by employer UUID"),
):
    """
    Full job list with applicant counts.
    Filterable by title search or specific employer.
    """
    try:
        q = supabase.table("jobs").select(
            "id, employer_id, title, company_name, job_city, "
            "salary_min, salary_max, openings, hiring_speed, created_at"
        )
        if search:
            q = q.ilike("title", f"%{search}%")
        if employer_id:
            q = q.eq("employer_id", employer_id)

        result = q.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
        jobs   = result.data or []

        for job in jobs:
            try:
                cnt                  = supabase.table("job_applications").select("id", count="exact").eq("job_id", job["id"]).execute()
                job["applicant_count"] = cnt.count or 0
            except Exception:
                job["applicant_count"] = None

        return {"status": "success", "count": len(jobs), "jobs": jobs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.patch("/jobs/{job_id}", dependencies=[Depends(require_admin)])
async def admin_update_job(job_id: str, body: AdminJobUpdate):
    """Edit any field on any job posting — admin override, no ownership check."""
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=422, detail="No fields provided to update.")
    try:
        res = supabase.table("jobs").update(updates).eq("id", job_id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Job not found.")
        return {"status": "success", "updated": res.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.delete("/jobs/{job_id}", dependencies=[Depends(require_admin)])
async def admin_delete_job(job_id: str):
    """
    Remove a job posting and all its applications.
    Use for spam, illegal, or inappropriate listings.
    """
    try:
        supabase.table("job_applications").delete().eq("job_id", job_id).execute()
        supabase.table("jobs").delete().eq("id", job_id).execute()
        return {"status": "success", "message": f"Job {job_id} and all its applications deleted."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete job: {str(e)}")


# ══════════════════════════════════════════════════════════════════════════════
# APPLICATION MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

@admin_router.get("/applications", dependencies=[Depends(require_admin)])
async def admin_list_applications(
    limit:  int           = Query(20, ge=1, le=100),
    offset: int           = Query(0, ge=0),
    job_id: Optional[str] = Query(None),
    email:  Optional[str] = Query(None, description="Filter by applicant email"),
):
    """All applications across the platform, with optional filters."""
    try:
        q = supabase.table("job_applications").select(
            "id, job_id, full_name, email, phone, cover_note, applied_at"
        )
        if job_id:
            q = q.eq("job_id", job_id)
        if email:
            q = q.ilike("email", f"%{email}%")

        result = q.order("applied_at", desc=True).range(offset, offset + limit - 1).execute()
        return {
            "status":       "success",
            "count":        len(result.data or []),
            "applications": result.data or [],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.delete("/applications/{application_id}", dependencies=[Depends(require_admin)])
async def admin_delete_application(application_id: str):
    """Remove a specific application (e.g., spam or abuse report)."""
    try:
        supabase.table("job_applications").delete().eq("id", application_id).execute()
        return {"status": "success", "message": f"Application {application_id} deleted."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ══════════════════════════════════════════════════════════════════════════════
# GLOBAL SEARCH
# ══════════════════════════════════════════════════════════════════════════════

@admin_router.get("/search", dependencies=[Depends(require_admin)])
async def admin_global_search(q: str = Query(..., min_length=2)):
    """
    Search across jobs, employers, and employees simultaneously.
    Ideal for the admin panel top-bar search box.
    """
    try:
        jobs = (
            supabase.table("jobs")
            .select("id, title, company_name, job_city, created_at")
            .ilike("title", f"%{q}%")
            .limit(5)
            .execute()
        ).data or []

        employers = (
            supabase.table("employers")
            .select("id, company_name, email, created_at")
            .ilike("company_name", f"%{q}%")
            .limit(5)
            .execute()
        ).data or []

        employees = (
            supabase.table("employees")
            .select("id, full_name, email, created_at")
            .ilike("full_name", f"%{q}%")
            .limit(5)
            .execute()
        ).data or []

        return {
            "status":  "success",
            "query":   q,
            "results": {
                "jobs":      jobs,
                "employers": employers,
                "employees": employees,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))