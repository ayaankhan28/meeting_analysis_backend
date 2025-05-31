from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean, Text, Integer, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from typing import Optional, List

import uuid
import enum
from datetime import datetime
from pydantic import BaseModel, EmailStr
from app.database import Base

# Enums
class MediaType(str, enum.Enum):
    VIDEO = 'video'
    AUDIO = 'audio'

class UploadStatus(str, enum.Enum):
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'

# SQLAlchemy Models
class User(Base):
    """Model for users."""
    
    __tablename__ = 'users'
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String)
    avatar_url: Mapped[Optional[str]] = mapped_column(String)
    auth_provider: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    media: Mapped[List["Media"]] = relationship(back_populates="user")

class Media(Base):
    """Model for media files."""
    
    __tablename__ = 'media'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    type: Mapped[MediaType] = mapped_column(Enum("video","audio",name="media_type_enum"), nullable=False)
    upload_status: Mapped[UploadStatus] = mapped_column(Enum("pending","processing","completed","failed",name="upload_status_enum"), nullable=False, default=UploadStatus.PENDING)
    duration: Mapped[Optional[int]] = mapped_column(Integer)
    language: Mapped[Optional[str]] = mapped_column(String(10))
    url: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user: Mapped["User"] = relationship(back_populates="media")

