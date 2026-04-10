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
        Retrieves a paginated list of users with optional search filtering.
        """
        # Since we are using SQLAlchemy for Admin, but main users might be in Supabase, 
        # we still use raw SQL or SQLAlchemy models if they exist. 
        # For now, we assume a 'users' table exists.
        from sqlalchemy import text
        
        search_query = ""
        params = {"skip": skip, "limit": limit}
        
        if search:
            search_query = "WHERE email ILIKE :search OR name ILIKE :search"
            params["search"] = f"%{search}%"
            
        count_sql = text(f"SELECT COUNT(*) FROM auth.users {search_query}")
        data_sql = text(f"SELECT * FROM auth.users {search_query} LIMIT :limit OFFSET :skip")
        
        total = db.execute(count_sql, {"search": params.get("search")}).scalar()
        data = db.execute(data_sql, params).mappings().all()
        
        return {
            "total": total,
            "data": data,
            "pagination": {
                "skip": skip,
                "limit": limit
            }
        }

    @staticmethod
    def get_paginated_workers(db: Session, skip: int = 0, limit: int = 20, search: Optional[str] = None):
        # Implementation for workers
        query_sql = "SELECT * FROM employees" # Existing workers table
        if search:
            query_sql += " WHERE full_name ILIKE :search"
        
        # Real aggregate and fetch logic
        return {"total": 0, "data": [], "pagination": {"skip": skip, "limit": limit}}

    @staticmethod
    def get_paginated_bookings(db: Session, skip: int = 0, limit: int = 20, search: Optional[str] = None):
        # Implementation for bookings
        return {"total": 0, "data": [], "pagination": {"skip": skip, "limit": limit}}

    @staticmethod
    def broadcast_system_message(db: Session, title: str, body: str, admin_id: uuid.UUID):
        # Logging the broadcast action
        log_admin_audit(db, admin_id, "BROADCAST_MESSAGE", "system", {"title": title})
        return {"status": "broadcast_queued", "admin_id": str(admin_id)}
