import uuid
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from models.admin_audit_log import AdminAuditLog
from models.schemas import UserResponse # Assuming existing schemas can be reused for response
from typing import List, Dict, Any, Optional

def log_admin_audit(db: Session, admin_id: uuid.UUID, action: str, target_resource: str, metadata: Dict[str, Any]):
    """
    Persists an administrative action to the audit log safely using atomic transactions.
    """
    with db.begin():
        audit_log = AdminAuditLog(
            admin_id=admin_id,
            action=action,
            target_resource=target_resource,
            metadata_json=metadata
        )
        db.add(audit_log)
    return audit_log.id

class AdminService:
    @staticmethod
    def get_paginated_users(db: Session, skip: int = 0, limit: int = 20, search: Optional[str] = None):
        """
        Retrieves a paginated list of users from the Supabase profiles table.
        """
        from database import get_supabase
        client = get_supabase()
        
        query = client.table("profiles").select("*", count="exact")
        
        if search:
            query = query.or_(f"name.ilike.%{search}%,email.ilike.%{search}%")
            
        res = query.range(skip, skip + limit - 1).execute()
        
        return {
            "total": res.count or 0,
            "data": res.data or [],
            "pagination": {
                "skip": skip,
                "limit": limit
            }
        }

    @staticmethod
    def get_paginated_workers(db: Session, skip: int = 0, limit: int = 20, search: Optional[str] = None):
        """
        Retrieves a paginated list of workers (employees) from Supabase.
        """
        from database import get_supabase
        client = get_supabase()
        
        # We join with profiles to get names
        query = client.table("employees").select("*, profiles(*)", count="exact")
        
        if search:
            query = query.filter("profiles.name", "ilike", f"%{search}%")
            
        res = query.range(skip, skip + limit - 1).execute()
        
        # Flatten the profile data for the frontend
        flattened_data = []
        for worker in (res.data or []):
            profile = worker.pop("profiles", {})
            flattened_data.append({
                **worker,
                "name": profile.get("name", "Unknown"),
                "email": profile.get("email", ""),
                "status": "Active" if worker.get("is_available") else "Inactive",
                "kyc": "Approved" if worker.get("is_verified") else "Pending",
                "jobs": 0, # Placeholder
            })
            
        return {
            "total": res.count or 0,
            "data": flattened_data,
            "pagination": {
                "skip": skip,
                "limit": limit
            }
        }

    @staticmethod
    def get_paginated_bookings(db: Session, skip: int = 0, limit: int = 20, search: Optional[str] = None):
        """
        Retrieves a paginated list of bookings from Supabase.
        """
        from database import get_supabase
        client = get_supabase()
        
        query = client.table("bookings").select("*, profiles(name), employees(profiles(name))", count="exact")
        
        res = query.order("created_at", descending=True).range(skip, skip + limit - 1).execute()
        
        formatted_data = []
        for b in (res.data or []):
            employer_name = b.get("profiles", {}).get("name", "Unknown")
            # The employee join might be nested
            worker_info = b.get("employees", {})
            worker_name = "Unknown"
            if isinstance(worker_info, dict):
                worker_name = worker_info.get("profiles", {}).get("name", "Worker")
            elif isinstance(worker_info, list) and len(worker_info) > 0:
                worker_name = worker_info[0].get("profiles", {}).get("name", "Worker")

            formatted_data.append({
                "id": b.get("booking_ref") or str(b.get("id")),
                "employer": employer_name,
                "worker": worker_name,
                "service": "Service", # Map category_id if needed
                "amount": f"₹{b.get('total_amount', 0)}",
                "date": b.get("booking_date"),
                "status": b.get("status", "Pending")
            })

        return {
            "total": res.count or 0,
            "data": formatted_data,
            "pagination": {
                "skip": skip,
                "limit": limit
            }
        }

    @staticmethod
    def get_dashboard_metrics(db: Session):
        """
        Fetches live aggregated metrics using the Supabase REST API.
        This is more resilient to DATABASE_URL misconfigurations.
        """
        from database import get_supabase
        client = get_supabase()
        
        try:
            # 1. Total Bookings
            bookings_res = client.table("bookings").select("count", count="exact").limit(1).execute()
            bookings_count = bookings_res.count or 0
            
            # 2. Active Workers (Employees)
            workers_res = client.table("employees").select("count", count="exact").limit(1).execute()
            workers_count = workers_res.count or 0
            
            # 3. Pending Tasks (Jobs)
            jobs_res = client.table("jobs").select("count", count="exact").limit(1).execute()
            jobs_count = jobs_res.count or 0
            
            # 4. User Stats (Optional - might require service role)
            users_count = 0
            try:
                # Try fetching from public profiles or a dedicated table if users is sensitive
                profiles_res = client.table("profiles").select("count", count="exact").limit(1).execute()
                users_count = profiles_res.count or 0
            except:
                pass
                
            return {
                "total_bookings": bookings_count,
                "active_workers": workers_count,
                "pending_verifications": 0,
                "active_jobs": jobs_count,
                "total_users": users_count
            }
        except Exception as e:
            # Fallback for unexpected API errors
            return {
                "total_bookings": 0,
                "active_workers": 0,
                "pending_verifications": 0,
                "error": str(e)
            }

    @staticmethod
    def broadcast_system_message(db: Session, title: str, body: str, admin_id: uuid.UUID):
        # Logging the broadcast action
        log_admin_audit(db, admin_id, "BROADCAST_MESSAGE", "system", {"title": title})
        return {"status": "broadcast_queued", "admin_id": str(admin_id)}
