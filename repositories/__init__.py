"""
Repositories package — data access layer for LaborGrow.

Each repository encapsulates all Supabase queries for a specific
domain entity, keeping service classes free of raw DB calls.
"""
from repositories.base_repository import BaseRepository
from repositories.worker_repository import WorkerRepository, CategoryRepository
from repositories.booking_repository import BookingRepository
from repositories.user_repository import UserRepository
from repositories.job_repository import JobRepository

__all__ = [
    "BaseRepository",
    "WorkerRepository",
    "CategoryRepository",
    "BookingRepository",
    "UserRepository",
    "JobRepository",
]
