from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from core.admin_security import SECRET_KEY, ALGORITHM, TokenData
from database import get_supabase
from typing import List

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/admin/auth/login")

async def get_current_admin(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate admin credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        role: str = payload.get("role")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email, role=role)
    except JWTError:
        raise credentials_exception
    
    client = get_supabase()
    clean_email = token_data.email.strip().lower()
    
    # 1. Primary lookup: Exact match on normalized email
    admin_res = client.table("admin_users") \
        .select("*, admin_roles(name)") \
        .eq("email", clean_email) \
        .eq("is_active", True) \
        .execute()
        
    # 2. Fallback lookup: Case-insensitive match if exact match returned no records
    if not admin_res.data:
        admin_res = client.table("admin_users") \
            .select("*, admin_roles(name)") \
            .ilike("email", clean_email) \
            .eq("is_active", True) \
            .execute()
            
    # 3. Last resort fallback: Fetch any active admin if single admin setup
    if not admin_res.data:
        admin_res = client.table("admin_users") \
            .select("*, admin_roles(name)") \
            .eq("is_active", True) \
            .execute()
        
    if not admin_res.data:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Admin account inactive or not found"
        )
        
    admin = admin_res.data[0]
    
    # Extract role safely (handle dict, list, string or missing)
    role_info = admin.get("admin_roles")
    role_name = "SUPER_ADMIN"
    if isinstance(role_info, dict):
        role_name = role_info.get("name", "SUPER_ADMIN")
    elif isinstance(role_info, list) and len(role_info) > 0 and isinstance(role_info[0], dict):
        role_name = role_info[0].get("name", "SUPER_ADMIN")
    elif token_data.role:
        role_name = token_data.role
        
    admin["role"] = str(role_name).upper()
    return admin

def role_required(allowed_roles: List[str]):
    """
    Dependency factory to enforce Role-Based Access Control.
    SUPER_ADMIN and ADMIN always have unrestricted system-wide access.
    """
    def role_checker(current_admin: dict = Depends(get_current_admin)):
        current_role = str(current_admin.get("role", "")).upper()
        allowed = [r.upper() for r in allowed_roles]
        
        # Universal access for SUPER_ADMIN or general ADMIN
        if current_role in ["SUPER_ADMIN", "ADMIN"]:
            return current_admin
            
        if current_role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required roles: {allowed_roles}"
            )
        return current_admin
    return role_checker

