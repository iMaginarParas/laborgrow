from fastapi import APIRouter, Depends, HTTPException, status
from core.admin_security import verify_password, create_access_token
from models.admin_schemas import AdminLogin, Token
from database import get_supabase
from datetime import datetime

router = APIRouter(prefix="/auth", tags=["Admin Authentication"])

@router.post("/login", response_model=Token)
async def admin_login(login_data: AdminLogin):
    client = get_supabase()
    
    # Fetch admin user along with their role name
    res = client.table("admin_users") \
        .select("*, admin_roles(name)") \
        .eq("email", login_data.email) \
        .execute()
        
    if not res.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid admin credentials"
        )
    
    admin = res.data[0]
    
    # Check password
    if not verify_password(login_data.password, admin["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid admin credentials"
        )

    # Check if active
    if not admin.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Account is disabled"
        )

    # Update last login timestamp
    client.table("admin_users") \
        .update({"last_login": datetime.now().isoformat()}) \
        .eq("id", admin["id"]) \
        .execute()

    role_name = admin["admin_roles"]["name"]
    
    # Generate JWT
    access_token = create_access_token(
        data={"sub": admin["email"], "role": role_name}
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": {
            "id": admin["id"],
            "email": admin["email"],
            "role": role_name,
            "is_active": admin["is_active"],
            "last_login": admin["last_login"]
        }
    }

@router.post("/logout")
async def admin_logout():
    """
    Logout is handled client-side by destroying the JWT, 
    but we provide the endpoint for architectural completeness.
    """
    return {"message": "Logged out successfully"}
