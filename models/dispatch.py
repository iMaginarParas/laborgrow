import uuid
import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Numeric, Boolean, DateTime, ForeignKey, Enum, Text, Integer, UUID
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base

class AvailabilityStatus(str, enum.Enum):
    OFFLINE = "OFFLINE"
    ONLINE = "ONLINE"
    BUSY = "BUSY"
    ON_BREAK = "ON_BREAK"

class DispatchStatus(str, enum.Enum):
    PENDING = "PENDING"
    DISPATCHING = "DISPATCHING"
    ASSIGNED = "ASSIGNED"
    FAILED = "FAILED"

class WorkerAvailability(Base):
    __tablename__ = "worker_availability"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worker_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, index=True)
    status: Mapped[AvailabilityStatus] = mapped_column(Enum(AvailabilityStatus), default=AvailabilityStatus.OFFLINE)
    current_latitude: Mapped[Optional[float]] = mapped_column(Numeric(precision=9, scale=6))
    current_longitude: Mapped[Optional[float]] = mapped_column(Numeric(precision=9, scale=6))
    last_seen_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    is_online: Mapped[bool] = mapped_column(default=False)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

class DispatchQueue(Base):
    __tablename__ = "dispatch_queue"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, index=True)
    status: Mapped[DispatchStatus] = mapped_column(Enum(DispatchStatus), default=DispatchStatus.PENDING)
    attempt_count: Mapped[int] = mapped_column(default=0)
    assigned_worker_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    last_attempt_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
