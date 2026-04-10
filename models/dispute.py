import uuid
import enum
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Enum, Text, ForeignKey, DateTime, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base

class DisputeStatus(str, enum.Enum):
    OPEN = "OPEN"
    UNDER_INVESTIGATION = "UNDER_INVESTIGATION"
    AWAITING_RESPONSE = "AWAITING_RESPONSE"
    RESOLVED = "RESOLVED"
    ESCALATED = "ESCALATED"
    CLOSED = "CLOSED"

class DisputeType(str, enum.Enum):
    NO_SHOW = "NO_SHOW"
    POOR_SERVICE = "POOR_SERVICE"
    DAMAGE = "DAMAGE"
    PAYMENT_ISSUE = "PAYMENT_ISSUE"
    SAFETY_CONCERN = "SAFETY_CONCERN"
    OTHER = "OTHER"

class Dispute(Base):
    __tablename__ = "disputes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, unique=True)
    reported_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    reported_role: Mapped[str] = mapped_column(String(20))
    dispute_type: Mapped[DisputeType] = mapped_column(Enum(DisputeType))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[DisputeStatus] = mapped_column(Enum(DisputeStatus), default=DisputeStatus.OPEN)
    assigned_admin_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

class DisputeMessage(Base):
    __tablename__ = "dispute_messages"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dispute_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("disputes.id"))
    sender_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    sender_role: Mapped[str] = mapped_column(String(20))
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

class DisputeEvidence(Base):
    __tablename__ = "dispute_evidence"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dispute_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("disputes.id"))
    file_url: Mapped[str] = mapped_column(Text)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

class DisputeLog(Base):
    __tablename__ = "dispute_logs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dispute_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("disputes.id"))
    previous_status: Mapped[DisputeStatus] = mapped_column(Enum(DisputeStatus))
    new_status: Mapped[DisputeStatus] = mapped_column(Enum(DisputeStatus))
    changed_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    reason: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
