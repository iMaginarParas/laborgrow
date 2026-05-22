import uuid
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base

class SystemSetting(Base):
    __tablename__ = "system_settings"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    value: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(50))
