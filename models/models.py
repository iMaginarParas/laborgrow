from sqlalchemy import String, Float, Integer, Boolean, ForeignKey, Text, DateTime, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from database import Base
import uuid
from typing import List, Optional

# Many-to-Many relationship for Workers and Categories
worker_categories = Table(
    "worker_categories",
    Base.metadata,
    Column("worker_id", ForeignKey("workers.id"), primary_key=True),
    Column("category_id", ForeignKey("categories.id"), primary_key=True),
)

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    profile_pic_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    worker_profile = relationship("Worker", back_populates="user", uselist=False)
    bookings = relationship("Booking", back_populates="customer")
    reviews = relationship("Review", back_populates="customer")

class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    emoji: Mapped[str] = mapped_column(String(10))
    slug: Mapped[str] = mapped_column(String(50), unique=True)

    workers = relationship("Worker", secondary=worker_categories, back_populates="categories")

class Worker(Base):
    __tablename__ = "workers"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[str] = mapped_column(String(100))
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)
    experience_years: Mapped[int] = mapped_column(Integer)
    hourly_rate: Mapped[float] = mapped_column(Float)
    min_hours: Mapped[int] = mapped_column(Integer, default=1)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="worker_profile")
    categories = relationship("Category", secondary=worker_categories, back_populates="workers")
    skills = relationship("WorkerSkill", back_populates="worker")
    bookings = relationship("Booking", back_populates="worker")
    reviews = relationship("Review", back_populates="worker")

class WorkerSkill(Base):
    __tablename__ = "worker_skills"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    worker_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workers.id"))
    skill_name: Mapped[str] = mapped_column(String(100))
    
    worker = relationship("Worker", back_populates="skills")

class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    worker_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workers.id"))
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    
    booking_date: Mapped[str] = mapped_column(String(20)) # YYYY-MM-DD
    time_slot: Mapped[str] = mapped_column(String(50))
    hours: Mapped[int] = mapped_column(Integer)
    address: Mapped[str] = mapped_column(Text)
    
    total_amount: Mapped[float] = mapped_column(Float)
    platform_fee: Mapped[float] = mapped_column(Float, default=50.0)
    discount_amount: Mapped[float] = mapped_column(Float, default=0.0)
    
    status: Mapped[str] = mapped_column(String(20), default="pending") # pending | confirmed | in_progress | completed | cancelled
    booking_ref: Mapped[str] = mapped_column(String(50), unique=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    customer = relationship("User", back_populates="bookings")
    worker = relationship("Worker", back_populates="bookings")
    payment = relationship("Payment", back_populates="booking", uselist=False)
    review = relationship("Review", back_populates="booking", uselist=False)
