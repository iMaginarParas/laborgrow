import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from supabase import create_client, Client

load_dotenv()

# Initialize Supabase
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_ANON_KEY")
service_key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

# We use the service key for registration to bypass RLS and create profile entries
supabase: Client = create_client(url, service_key)

app = FastAPI(title="Job Portal Backend")

# --- Schemas ---
class EmployerRegister(BaseModel):
    email: EmailStr
    password: str
    company_name: str

class JobCreate(BaseModel):
    title: str
    description: str
    location: str
    employer_id: str # The UUID from Supabase Auth

# --- Endpoints ---

@app.post("/register")
async def register_employer(user: EmployerRegister):
    # 1. Create the user in Supabase Auth
    try:
        auth_response = supabase.auth.sign_up({
            "email": user.email,
            "password": user.password,
        })
        
        if not auth_response.user:
            raise HTTPException(status_code=400, detail="Registration failed")

        # 2. Insert into a custom 'employers' table to store company info
        profile_data = {
            "id": auth_response.user.id,
            "company_name": user.company_name,
            "email": user.email
        }
        supabase.table("employers").insert(profile_data).execute()

        return {"message": "Employer created", "user_id": auth_response.user.id}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/jobs")
async def post_job(job: JobCreate):
    try:
        response = supabase.table("jobs").insert({
            "title": job.title,
            "description": job.description,
            "location": job.location,
            "employer_id": job.employer_id
        }).execute()
        
        return {"message": "Job posted successfully", "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/")
def health_check():
    return {"status": "online"}