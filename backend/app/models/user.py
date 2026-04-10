"""
User Model
Represents system users: parents, schools, psychologists, admin
"""

from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base


class UserRole(str, enum.Enum):
    """User roles in the system"""
    PARENT = "PARENT"
    SCHOOL = "SCHOOL"
    PSYCHOLOGIST = "PSYCHOLOGIST"
    ADMIN = "ADMIN"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)
    role = Column(SQLEnum(UserRole), nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(50))
    organization = Column(String(255))
    is_active = Column(Boolean, default=True, index=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"
