"""
Repositories package — data access layer for LaborGrow.

Each repository encapsulates all Supabase queries for a specific
domain entity, keeping service classes free of raw DB calls.
"""
from .base_repository import BaseRepository
from .worker_repository import WorkerRepository, CategoryRepository
from .booking_repository import BookingRepository
from .user_repository import UserRepository
from .job_repository import JobRepository

__all__ = [
    "BaseRepository",
    "WorkerRepository",
    "CategoryRepository",
    "BookingRepository",
    "UserRepository",
    "JobRepository",
]
