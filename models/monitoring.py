import uuid
import enum
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import String, Enum, Text, ForeignKey, DateTime, Integer, Numeric, JSON, Boolean, UUID
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base

class SystemEventType(str, enum.Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    CRITICAL = "CRITICAL"

class ServiceType(str, enum.Enum):
    API = "API"
    DISPATCH = "DISPATCH"
    NOTIFICATION = "NOTIFICATION"
    DATABASE = "DATABASE"
    WORKER = "WORKER"
    SCHEDULER = "SCHEDULER"

class SystemEvent(Base):
    __tablename__ = "system_events"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_type: Mapped[ServiceType] = mapped_column(Enum(ServiceType))
    event_type: Mapped[SystemEventType] = mapped_column(Enum(SystemEventType))
    message: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, index=True)

class ErrorLog(Base):
    __tablename__ = "error_logs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_name: Mapped[str] = mapped_column(String(100))
    error_message: Mapped[str] = mapped_column(Text)
    stack_trace: Mapped[Optional[str]] = mapped_column(Text)
    request_path: Mapped[Optional[str]] = mapped_column(String(255))
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, index=True)

class PerformanceMetric(Base):
    __tablename__ = "performance_metrics"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_name: Mapped[str] = mapped_column(String(100))
    endpoint: Mapped[str] = mapped_column(String(255))
    response_time_ms: Mapped[float] = mapped_column(Numeric(10, 2))
    status_code: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, index=True)
