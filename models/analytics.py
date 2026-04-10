import uuid
from datetime import datetime, date
from sqlalchemy import String, Integer, Numeric, Date, DateTime, ForeignKey, Text, UUID
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base

class DailyMetric(Base):
    __tablename__ = "daily_metrics"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date: Mapped[date] = mapped_column(Date, unique=True, index=True)
    total_bookings: Mapped[int] = mapped_column(default=0)
    completed_bookings: Mapped[int] = mapped_column(default=0)
    cancelled_bookings: Mapped[int] = mapped_column(default=0)
    failed_bookings: Mapped[int] = mapped_column(default=0)
    active_workers: Mapped[int] = mapped_column(default=0)
    online_workers: Mapped[int] = mapped_column(default=0)
    busy_workers: Mapped[int] = mapped_column(default=0)
    average_worker_rating: Mapped[float] = mapped_column(Numeric(3, 2), default=0.0)
    average_job_duration_minutes: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0)
    dispatch_success_rate: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0)
    cancellation_rate: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0)
    dispute_rate: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0)
    notifications_sent: Mapped[int] = mapped_column(default=0)
    notifications_failed: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

class WorkerPerformanceMetric(Base):
    __tablename__ = "worker_performance_metrics"
    worker_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    total_jobs_completed: Mapped[int] = mapped_column(default=0)
    total_jobs_failed: Mapped[int] = mapped_column(default=0)
    average_rating: Mapped[float] = mapped_column(Numeric(3, 2), default=0.0)
    average_job_duration_minutes: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0)
    last_updated: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

class ReportExport(Base):
    __tablename__ = "report_exports"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_type: Mapped[str] = mapped_column(String(50))
    generated_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    file_url: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
