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
                        "role": user_in.city if user_in.city in ["employer", "employee"] else "employee" # Simple role assignment
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
                "user": auth_response.user,
                "profile": profile_response.data[0] if profile_response.data else None,
                "role": role
            }
            
        except Exception as e:
            if "already registered" in str(e).lower() or "already exists" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This email is already registered. Please login or use another email."
                )
            # Log the real error internally and let the global handler report a polite 500
            logger.error(f"Internal registration error: {str(e)}")
            raise e

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
    async def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch the user profile from employees or employers table.
        """
        # Try employees first
        res = supabase.table("employees").select("*").eq("id", user_id).execute()
        if res.data:
            return res.data[0]
        
        # Try employers
        res = supabase.table("employers").select("*").eq("id", user_id).execute()
        if res.data:
            return res.data[0]
            
        return None

