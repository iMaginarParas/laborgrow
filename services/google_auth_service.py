"""
Google OAuth Authentication Service.

Verifies Google ID tokens and creates/authenticates users via Supabase.
"""
import httpx
from typing import Dict, Any, Optional
from fastapi import HTTPException, status

from database import get_supabase
from core.logger import logger
from repositories.user_repository import UserRepository


GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"


class GoogleAuthService:
    """
    Handles Google Sign-In server-side verification and Supabase user management.
    """
    _user_repo = UserRepository()

    @staticmethod
    async def verify_google_token(id_token: str) -> Dict[str, Any]:
        """
        Verify a Google ID token via Google's tokeninfo endpoint.
        Returns the decoded token payload (email, name, picture, sub).
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                GOOGLE_TOKENINFO_URL,
                params={"id_token": id_token},
            )

        if response.status_code != 200:
            logger.error("Google token verification failed", status_code=response.status_code)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Google token. Please try signing in again.",
            )

        payload = response.json()

        # Ensure the token contains an email
        if not payload.get("email"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google account does not have an email address.",
            )

        return payload

    @staticmethod
    async def authenticate_with_google(
        id_token: str,
        role: str = "employer",
    ) -> Dict[str, Any]:
        """
        Full Google Sign-In flow:
        1. Verify the Google ID token
        2. Check if user exists in Supabase Auth
        3. Sign in (or sign up) via Supabase
        4. Ensure a profile row exists in employers/employees
        5. Return access + refresh tokens
        """
        # Step 1: Verify the token with Google
        google_payload = await GoogleAuthService.verify_google_token(id_token)

        email = google_payload["email"]
        name = google_payload.get("name", "User")
        picture = google_payload.get("picture")

        try:
            client = get_supabase()

            # Step 2: Use native Supabase ID token sign in.
            # This verifies the token, creates the user if they don't exist,
            # and performs native account linking WITHOUT overwriting their password.
            auth_response = client.auth.sign_in_with_id_token({
                "provider": "google",
                "token": id_token
            })

            user = auth_response.user
            session = auth_response.session

            if not user or not session:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to authenticate with Google. Please try again.",
                )

            # Step 3: Ensure profile row exists
            user_id = str(user.id)
            existing_profile = await GoogleAuthService._user_repo.find_profile(user_id)

            if not existing_profile:
                # Create the profile
                role_resolved = "employer" if role in ["employer", "hire"] else "employee"
                table_name = "employers" if role_resolved == "employer" else "employees"

                profile_data: Dict[str, Any] = {
                    "id": user_id,
                    "email": email,
                }

                if table_name == "employers":
                    profile_data["company_name"] = name
                else:
                    profile_data["full_name"] = name
                    profile_data["phone"] = ""

                if picture:
                    if table_name != "employers":
                        profile_data["profile_pic_url"] = picture
                await GoogleAuthService._user_repo.update_profile(
                    user_id, table_name, profile_data
                )

            return {
                "access_token": session.access_token,
                "refresh_token": session.refresh_token,
                "token_type": "bearer",
                "user_id": user_id,
                "email": email,
                "name": name,
                "is_new_user": existing_profile is None,
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Google authentication error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Google sign-in failed. Please try again later.",
            )
