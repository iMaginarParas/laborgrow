from .auth import router as auth_router
from .workers import router as workers_router, cat_router as categories_router
from .bookings import router as bookings_router
from .jobs import router as jobs_router
from .admin import router as admin_router
from .applications import router as applications_router
from .reviews import router as reviews_router
from .hire import router as hire_router
from .worker_dashboard import router as worker_dashboard_router
from .notifications import router as notifications_router
from .chat_router import router as chat_router

__all__ = [
    "auth_router",
    "workers_router",
    "categories_router",
    "bookings_router",
    "jobs_router",
    "admin_router",
    "applications_router",
    "reviews_router",
    "hire_router",
    "worker_dashboard_router",
    "notifications_router",
    "chat_router"
]

