import uuid
import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Enum, Text, ForeignKey, DateTime, Integer, UUID, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base

class NotificationChannel(str, enum.Enum):
    PUSH = "PUSH"
    SMS = "SMS"
    EMAIL = "EMAIL"
    IN_APP = "IN_APP"

class NotificationStatus(str, enum.Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    RETRYING = "RETRYING"

class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recipient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    recipient_type: Mapped[str] = mapped_column(String(20))
    channel: Mapped[NotificationChannel] = mapped_column(Enum(NotificationChannel))
    title: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text)
    status: Mapped[NotificationStatus] = mapped_column(Enum(NotificationStatus), default=NotificationStatus.PENDING)
    retry_count: Mapped[int] = mapped_column(default=0)
    scheduled_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    sent_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

class NotificationTemplate(Base):
    __tablename__ = "notification_templates"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    channel: Mapped[NotificationChannel] = mapped_column(Enum(NotificationChannel))
    template_title: Mapped[str] = mapped_column(String(255))
    template_body: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
