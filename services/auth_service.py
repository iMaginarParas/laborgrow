from typing import Optional, Any, Dict
from fastapi import HTTPException, status

from database import get_supabase
from core.logger import logger
from models.schemas import UserCreate, LoginRequest
from repositories.user_repository import UserRepository

class AuthService:
    """
    High-level business logic for user authentication.
    Powered by Supabase Auth and de-coupled Repository access.
    """
    _user_repo = UserRepository()

    @staticmethod
    async def register_user(user_in: UserCreate) -> Dict[str, Any]:
        """
        Coordinate user registration.
        """
        try:
            client = await get_supabase()
            # 1. Sign up with Supabase Auth
            auth_response = await client.auth.sign_up({
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
                user_data["phone"] = user_in.phone
            else:
                user_data["full_name"] = user_in.name
                user_data["phone"] = user_in.phone
                user_data["city"] = user_in.city
            
            profile = await AuthService._user_repo.update_profile(auth_response.user.id, table_name, user_data)
            
            return {
                "user_id": str(auth_response.user.id),
                "email": auth_response.user.email,
                "profile": profile,
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
        """
        try:
            client = await get_supabase()
            identifier = login_in.phone_or_email.strip()
            if "@" in identifier:
                auth_data = {"email": identifier, "password": login_in.password}
            else:
                # Format phone number for Supabase
                phone_number = identifier
                if len(phone_number) == 10 and not phone_number.startswith("+"):
                    phone_number = f"+91{phone_number}"
                auth_data = {"phone": phone_number, "password": login_in.password}
            
            response = await client.auth.sign_in_with_password(auth_data)
            
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
        Identify user role and apply updates.
        """
        current_profile = await AuthService._user_repo.find_profile(user_id)
        if not current_profile:
            return None
            
        role = current_profile.get("role")
        is_employee = role == "employee"
        table_name = "employees" if is_employee else "employers"
        
        # Map frontend field names to database columns
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
            if "category_ids" in updates:
                work_details_updates["category_ids"] = updates["category_ids"]
            if "experience_years" in updates:
                work_details_updates["experience_years"] = updates["experience_years"]
            if "hourly_rate" in updates:
                work_details_updates["hourly_rate"] = updates["hourly_rate"]

            if work_details_updates:
                existing_details = current_profile.get("work_details")
                if not isinstance(existing_details, dict):
                    existing_details = {}
                existing_details.update(work_details_updates)
                db_updates["work_details"] = existing_details

        if not db_updates:
            return await AuthService.get_user_profile(user_id)

        # Apply updates
        result = await AuthService._user_repo.update_profile(user_id, table_name, db_updates)
        
        if result:
            return await AuthService.get_user_profile(user_id)
        return None

    @staticmethod
    async def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
        """
        Unified profile retriever.
        """
        profile = await AuthService._user_repo.find_profile(user_id)
        if profile:
            role = profile.get("role")
            profile["name"] = profile.get("full_name") or profile.get("company_name") or (
                "Worker" if role == "employee" else "Customer"
            )
            profile["phone"] = profile.get("phone") or "0000000000"
            profile["city"] = profile.get("city") or ""
            return profile
            
        return None
