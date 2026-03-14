"""
Unit tests for WorkerService._format_worker.
"""
import pytest
from services.worker_service import WorkerService


_BASE_ROW = {
    "id": "abc-123",
    "full_name": "Ravi Kumar",
    "email": "ravi@example.com",
    "phone": "9876543210",
    "profile_pic_url": None,
    "created_at": "2024-01-01T00:00:00",
    "city": "Bengaluru",
    "lat": 12.9716,
    "lng": 77.5946,
    "rating": 4.8,
    "is_verified": True,
    "is_available": True,
    "work_details": {
        "hourly_rate": 600.0,
        "experience_years": 3,
        "bio": "Experienced plumber",
        "min_hours": 2,
    },
    "skills": ["Plumbing", "Pipe fitting"],
}


class TestFormatWorker:
    def test_basic_fields(self):
        result = WorkerService._format_worker(_BASE_ROW)
        assert result["id"]       == "abc-123"
        assert result["city"]     == "Bengaluru"
        assert result["rating"]   == 4.8
        assert result["min_hours"] == 2

    def test_work_details_precedence(self):
        result = WorkerService._format_worker(_BASE_ROW)
        assert result["hourly_rate"]      == 600.0
        assert result["experience_years"] == 3
        assert result["bio"]              == "Experienced plumber"

    def test_skills_formatted(self):
        result = WorkerService._format_worker(_BASE_ROW)
        assert len(result["skills"]) == 2
        assert result["skills"][0]   == {"skill_name": "Plumbing"}

    def test_default_category_when_no_map(self):
        result = WorkerService._format_worker(_BASE_ROW)
        assert len(result["categories"]) == 1
        assert result["categories"][0]["slug"] == "general"

    def test_category_resolved_from_map(self):
        cats_map = {5: {"id": 5, "name": "Plumbing", "emoji": "🔧", "slug": "plumbing"}}
        row = dict(_BASE_ROW)
        row["work_details"] = {**_BASE_ROW["work_details"], "category_ids": [5]}
        result = WorkerService._format_worker(row, cats_map)
        assert result["categories"][0]["slug"] == "plumbing"

    def test_null_user_fields_no_crash(self):
        sparse_row = {
            "id": "xyz",
            "full_name": None,
            "email": None,
            "phone": None,
            "profile_pic_url": None,
            "created_at": None,
            "work_details": None,
            "skills": None,
        }
        result = WorkerService._format_worker(sparse_row)
        assert result["user"]["name"]  == "Worker"
        assert result["hourly_rate"]   == 500.0
        assert result["skills"]        == []
