from typing import Optional, Any, Dict
from fastapi import HTTPException, status
from supabase import Client

from database import supabase
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
                        "phone": user_in.phone
                    }
                }
            })
            
            if not auth_response.user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Registration failed with Supabase Auth."
                )
            
            # 2. Insert profile into public.users table
            # Supabase might handle this with a trigger, but we'll do it explicitly here for control
            user_data = {
                "id": auth_response.user.id,
                "name": user_in.name,
                "email": user_in.email,
                "phone": user_in.phone,
                "profile_pic_url": user_in.profile_pic_url,
                "address": user_in.address,
                "city": user_in.city
            }
            
            profile_response = supabase.table("users").insert(user_data).execute()
            
            return {
                "user": auth_response.user,
                "profile": profile_response.data[0] if profile_response.data else None
            }
            
        except Exception as e:
            if "already registered" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this email already exists."
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Registration failed: {str(e)}"
            )

    @staticmethod
    async def authenticate_user(login_in: LoginRequest) -> Dict[str, Any]:
        """
        Validate credentials via Supabase Auth.
        """
        try:
            # Login via Supabase
            # Note: Supabase sign_in_with_password primarily uses email
            # If the user provides a phone number, we'd need to handle that differently or expect email.
            # For now, we'll try to use the phone_or_email as email.
            
            response = supabase.auth.sign_in_with_password({
                "email": login_in.phone_or_email,
                "password": login_in.password
            })
            
            return {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "token_type": response.session.token_type,
                "user": response.user
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials or authentication failed."
            )

    @staticmethod
    async def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch the user profile from the public.users table.
        """
        response = supabase.table("users").select("*").eq("id", user_id).execute()
        return response.data[0] if response.data else None

