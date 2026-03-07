from .auth import router as auth_router
from .workers import router as workers_router, cat_router as categories_router
from .bookings import router as bookings_router
from .jobs import router as jobs_router
from .admin import router as admin_router

__all__ = [
    "auth_router",
    "workers_router",
    "categories_router",
    "bookings_router",
    "jobs_router",
    "admin_router"
]
