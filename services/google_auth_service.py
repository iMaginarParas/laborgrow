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

            # Step 2: Try to sign in with a deterministic password derived from
            # the Google sub (the user never types this — it's only for Supabase
            # internal auth). If the user doesn't exist yet, we create them.
            google_sub = google_payload.get("sub", "")
            # Use a long, deterministic password the user never sees
            internal_password = f"google_{google_sub}_laborgro_oauth"

            try:
                # Attempt sign-in first (existing user)
                auth_response = client.auth.sign_in_with_password({
                    "email": email,
                    "password": internal_password,
                })
            except Exception:
                # User doesn't exist — create them
                try:
                    auth_response = client.auth.sign_up({
                        "email": email,
                        "password": internal_password,
                        "options": {
                            "data": {
                                "name": name,
                                "role": role,
                                "provider": "google",
                                "avatar_url": picture,
                            }
                        },
                    })
                except Exception as signup_err:
                    err_msg = str(signup_err).lower()
                    if "already registered" in err_msg or "already exists" in err_msg:
                        # Account Linking: The user exists but hasn't linked Google yet.
                        # We verify they own the email via Google Token, then sync their
                        # internal password to allow Google Login to proceed.
                        logger.info("Syncing existing account with Google sign-in", email=email)
                        
                        existing_profile = await GoogleAuthService._user_repo.find_profile_by_email(email)
                        if existing_profile:
                            user_id = existing_profile["id"]
                            # Sync the password via Admin API
                            client.auth.admin.update_user_by_id(
                                user_id, 
                                {"password": internal_password}
                            )
                            # Retry sign-in
                            auth_response = client.auth.sign_in_with_password({
                                "email": email,
                                "password": internal_password,
                            })
                        else:
                            # User exists in auth.users but no profile found.
                            # We might need to find the user ID from auth.users directly.
                            # For safety, we'll try to update them if we can find them.
                            raise HTTPException(
                                status_code=status.HTTP_409_CONFLICT,
                                detail="This email is already registered. Please sign in with your email/password first to link Google."
                            )
                    else:
                        raise

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
