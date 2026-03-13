from typing import Optional, Any, Dict
from fastapi import HTTPException, status
from supabase import Client

from database import supabase
from core.logger import logger
from models.schemas import UserCreate, LoginRequest

class AuthService:
    """
    High-level business logic for user authentication using Supabase Auth.
    """

    @staticmethod
    async def register_user(user_in: UserCreate) -> Dict[str, Any]:
        """
        Coordinate user registration using Supabase Auth and profile creation.
        """
        try:
            # 1. Sign up with Supabase Auth
            auth_response = supabase.auth.sign_up({
                "email": user_in.email,
                "password": user_in.password,
                "options": {
                    "data": {
                        "name": user_in.name,
                        "phone": user_in.phone,
                        "role": user_in.role if user_in.role in ["employer", "employee"] else "employee"
                    }
                }
            })
            
            if not auth_response.user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Registration failed with Supabase Auth."
                )
            
            # 2. Insert profile based on role
            role = auth_response.user.user_metadata.get("role", "employee")
            table_name = "employers" if role == "employer" else "employees"
            
            user_data = {
                "id": auth_response.user.id,
                "email": user_in.email
            }
            if role == "employer":
                user_data["company_name"] = user_in.name
            else:
                user_data["full_name"] = user_in.name
                user_data["phone"] = user_in.phone
                user_data["city"] = user_in.city
            
            profile_response = supabase.table(table_name).insert(user_data).execute()
            
            return {
                "user_id": str(auth_response.user.id),
                "email": auth_response.user.email,
                "profile": profile_response.data[0] if profile_response.data else None,
                "role": role
            }
            
        except Exception as e:
            err_msg = str(e).lower()
            if "already registered" in err_msg or "already exists" in err_msg:
                friendly_err = "This email is already registered. Please login or use another email."
            elif "password" in err_msg and "short" in err_msg:
                friendly_err = "Your password is too short. Please use at least 6 characters."
            else:
                friendly_err = "We couldn't create your account right now. Please try again later."
            
            logger.error(f"Registration error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=friendly_err
            )

    @staticmethod
    async def authenticate_user(login_in: LoginRequest) -> Dict[str, Any]:
        """
        Validate credentials via Supabase Auth.
        Supports both email and phone number login.
        """
        try:
            identifier = login_in.phone_or_email.strip()
            # Simple check: if it contains '@', assume email; otherwise assume phone
            if "@" in identifier:
                auth_data = {"email": identifier, "password": login_in.password}
            else:
                # Format phone number for Supabase (e.g., adding +91 if missing and 10 digits)
                phone_number = identifier
                if len(phone_number) == 10 and not phone_number.startswith("+"):
                    phone_number = f"+91{phone_number}" # Default to India for this demo
                auth_data = {"phone": phone_number, "password": login_in.password}
            
            response = supabase.auth.sign_in_with_password(auth_data)
            
            return {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "token_type": response.session.token_type,
                "user": response.user
            }
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials. Please check your email/phone and password."
            )

    @staticmethod
    async def update_user_profile(user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Identify user role and apply updates to the correct profile table.
        """
        # 1. Determine role by checking both tables (or use auth metadata if preferred)
        is_employee = supabase.table("employees").select("id").eq("id", user_id).execute().data
        table_name = "employees" if is_employee else "employers"
        
        # 2. Map frontend field names to database columns
        db_updates = {}
        work_details_updates = {}
        
        if "name" in updates:
            db_updates["full_name" if is_employee else "company_name"] = updates["name"]
        if "phone" in updates:
            db_updates["phone"] = updates["phone"]
        if "city" in updates:
            db_updates["city"] = updates["city"]
        if "profile_pic_url" in updates:
            db_updates["profile_pic_url"] = updates["profile_pic_url"]

        if is_employee:
            if "skills" in updates:
                db_updates["skills"] = updates["skills"]
            if "bio" in updates:
                work_details_updates["bio"] = updates["bio"]
            if "experience_years" in updates:
                work_details_updates["experience_years"] = updates["experience_years"]
            if "hourly_rate" in updates:
                work_details_updates["hourly_rate"] = updates["hourly_rate"]

            if work_details_updates:
                # Merge with existing work_details
                existing = supabase.table("employees").select("work_details").eq("id", user_id).execute().data
                existing_details = existing[0].get("work_details") if existing else {}
                if not isinstance(existing_details, dict):
                    existing_details = {}
                existing_details.update(work_details_updates)
                db_updates["work_details"] = existing_details

        if not db_updates:
            return await AuthService.get_user_profile(user_id)

        # 3. Apply updates
        result = supabase.table(table_name).update(db_updates).eq("id", user_id).execute()
        
        if result.data:
            return await AuthService.get_user_profile(user_id)
        return None
    @staticmethod
    async def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch and unify profile from employees or employers table.
        Adds 'name' field for frontend compatibility.
        """
        # Try employees first
        res = supabase.table("employees").select("*").eq("id", user_id).execute()
        if res.data:
            profile = res.data[0]
            profile["name"] = profile.get("full_name") or "Worker"
            profile["phone"] = profile.get("phone") or "0000000000"
            profile["city"] = profile.get("city") or ""
            return profile
        
        # Try employers
        res = supabase.table("employers").select("*").eq("id", user_id).execute()
        if res.data:
            profile = res.data[0]
            profile["name"] = profile.get("company_name") or "Customer"
            profile["phone"] = profile.get("phone") or "0000000000"
            profile["city"] = profile.get("city") or ""
            return profile
            
        return None
