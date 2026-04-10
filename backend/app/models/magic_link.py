"""
Magic Link Token Model
For passwordless login via email links
"""

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timedelta, timezone

from app.core.database import Base


class MagicLinkToken(Base):
    """Magic link tokens for passwordless authentication"""
    __tablename__ = "magic_link_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    assignment_id = Column(UUID(as_uuid=True), ForeignKey("assessment_assignments.id", ondelete="SET NULL"), nullable=True)
    purpose = Column(String(50), default="login")  # "login" | "assessment_invite" | "password_reset"
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship to user
    user = relationship("User", backref="magic_links", passive_deletes=True)

    def is_valid(self) -> bool:
        """Check if token is still valid"""
        if self.used_at is not None:
            return False
        if datetime.now(timezone.utc) > self.expires_at:
            return False
        return True

    def __repr__(self):
        return f"<MagicLinkToken {self.token[:8]}... for user {self.user_id}>"
