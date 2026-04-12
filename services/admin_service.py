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
        Retrieves a paginated list of users by combining employees and employers tables.
        """
        from database import get_supabase
        client = get_supabase()
        
        # In a split-table architecture, we fetch from both and merge. 
        # For simplicity in pagination, we'll fetch 'limit' from each and then slice.
        
        emp_query = client.table("employees").select("*")
        host_query = client.table("employers").select("*")
        
        if search:
            emp_query  = emp_query.or_(f"full_name.ilike.%{search}%,email.ilike.%{search}%")
            host_query = host_query.or_(f"company_name.ilike.%{search}%,email.ilike.%{search}%")
            
        # Fetching a bit more to allow for merging
        emp_res  = emp_query.range(skip, skip + limit - 1).execute()
        host_res = host_query.range(skip, skip + limit - 1).execute()
        
        users = []
        for e in (emp_res.data or []):
            users.append({
                "id": e.get("id"),
                "name": e.get("full_name") or "Worker",
                "email": e.get("email"),
                "role": "Worker",
                "status": "Active" if e.get("is_available") else "Inactive",
                "bookings": 0,
                "joined": e.get("created_at")[:10] if e.get("created_at") else "—"
            })
            
        for h in (host_res.data or []):
            users.append({
                "id": h.get("id"),
                "name": h.get("company_name") or "Employer",
                "email": h.get("email"),
                "role": "Employer",
                "status": "Active",
                "bookings": 0,
                "joined": h.get("created_at")[:10] if h.get("created_at") else "—"
            })
            
        # Sort by ID or date if needed, then take the limit
        return {
            "total": (emp_res.count or 0) + (host_res.count or 0),
            "data": users[:limit],
            "pagination": {"skip": skip, "limit": limit}
        }

    @staticmethod
    def get_paginated_workers(db: Session, skip: int = 0, limit: int = 20, search: Optional[str] = None):
        """
        Retrieves a paginated list of workers (employees) from Supabase.
        """
        from database import get_supabase
        client = get_supabase()
        
        query = client.table("employees").select("*", count="exact")
        
        if search:
            query = query.or_(f"full_name.ilike.%{search}%,email.ilike.%{search}%")
            
        res = query.range(skip, skip + limit - 1).execute()
        
        flattened_data = []
        for worker in (res.data or []):
            flattened_data.append({
                **worker,
                "name": worker.get("full_name", "Unknown"),
                "email": worker.get("email", ""),
                "status": "Active" if worker.get("is_available") else "Inactive",
                "kyc": "Approved" if worker.get("is_verified") else "Pending",
                "jobs": 0,
            })
            
        return {
            "total": res.count or 0,
            "data": flattened_data,
            "pagination": {"skip": skip, "limit": limit}
        }

    @staticmethod
    def get_paginated_bookings(db: Session, skip: int = 0, limit: int = 20, search: Optional[str] = None):
        """
        Retrieves a paginated list of bookings from Supabase.
        """
        from database import get_supabase
        client = get_supabase()
        
        # We join with employees (worker) and employers (customer)
        # Note: 'profiles' join is replaced with direct 'employees' and 'employers' lookups
        query = client.table("bookings").select("*, employees(full_name), employers(company_name)", count="exact")
        
        res = query.order("created_at", descending=True).range(skip, skip + limit - 1).execute()
        
        formatted_data = []
        for b in (res.data or []):
            employer_info = b.get("employers")
            worker_info   = b.get("employees")
            
            employer_name = "Unknown"
            if isinstance(employer_info, dict): employer_name = employer_info.get("company_name", "Employer")
            
            worker_name = "Unknown"
            if isinstance(worker_info, dict): worker_name = worker_info.get("full_name", "Worker")

            formatted_data.append({
                "id": b.get("booking_ref") or str(b.get("id")),
                "employer": employer_name,
                "worker": worker_name,
                "service": "Service",
                "amount": f"₹{b.get('total_amount', 0)}",
                "date": b.get("booking_date"),
                "status": b.get("status", "Pending")
            })

        return {
            "total": res.count or 0,
            "data": formatted_data,
            "pagination": {"skip": skip, "limit": limit}
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
            
            # 4. Total Users (Employees + Employers)
            users_count = 0
            try:
                emp_count_res = client.table("employees").select("id", count="exact").limit(1).execute()
                host_count_res = client.table("employers").select("id", count="exact").limit(1).execute()
                users_count = (emp_count_res.count or 0) + (host_count_res.count or 0)
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
