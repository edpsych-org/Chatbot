"""
Verification Token Model
Stores secure tokens and OTP codes for parent assessment access verification
"""

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import uuid

from app.core.database import Base


class VerificationToken(Base):
    """
    Stores secure tokens and OTP codes for multi-layer verification

    Workflow:
    1. Psychologist assigns assessment -> generates secure_token + otp_code
    2. Parent receives link: /verify-access/{secure_token}
    3. Parent enters OTP -> validates otp_code
    4. Parent enters DOB -> validates date_of_birth
    5. Token marked as verified -> grants access to assessment
    """
    __tablename__ = "verification_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Secure token (URL-safe, 32 characters)
    secure_token = Column(String(255), unique=True, nullable=False, index=True)

    # OTP code (6 digits)
    otp_code = Column(String(6), nullable=False)

    # Related entities
    assignment_id = Column(UUID(as_uuid=True), ForeignKey("assessment_assignments.id"), nullable=False, index=True)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False, index=True)
    parent_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # Verification status
    is_otp_verified = Column(Boolean, default=False, nullable=False)
    is_dob_verified = Column(Boolean, default=False, nullable=False)
    is_fully_verified = Column(Boolean, default=False, nullable=False)

    # Expiration
    expires_at = Column(DateTime, nullable=False)  # Default: 7 days from creation

    # Verification attempts tracking
    otp_attempts = Column(String, default=0, nullable=False)  # Counter for failed OTP attempts
    dob_attempts = Column(String, default=0, nullable=False)  # Counter for failed DOB attempts

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    otp_verified_at = Column(DateTime, nullable=True)
    dob_verified_at = Column(DateTime, nullable=True)
    fully_verified_at = Column(DateTime, nullable=True)

    # Metadata
    ip_address = Column(String(50), nullable=True)  # IP address of verification request
    user_agent = Column(Text, nullable=True)  # Browser user agent

    # Relationships
    assignment = relationship("AssessmentAssignment", back_populates="verification_token")
    student = relationship("Student")
    parent = relationship("User")

    def is_expired(self) -> bool:
        """Check if token has expired"""
        return datetime.utcnow() > self.expires_at

    def is_valid(self) -> bool:
        """Check if token is valid and not expired"""
        return not self.is_expired() and not self.is_fully_verified

    def can_attempt_otp(self, max_attempts: int = 5) -> bool:
        """Check if OTP can be attempted (not exceeded max attempts)"""
        return int(self.otp_attempts) < max_attempts

    def can_attempt_dob(self, max_attempts: int = 3) -> bool:
        """Check if DOB can be attempted (not exceeded max attempts)"""
        return int(self.dob_attempts) < max_attempts

    def increment_otp_attempts(self):
        """Increment failed OTP attempts counter"""
        self.otp_attempts = str(int(self.otp_attempts) + 1)

    def increment_dob_attempts(self):
        """Increment failed DOB attempts counter"""
        self.dob_attempts = str(int(self.dob_attempts) + 1)

    def mark_otp_verified(self):
        """Mark OTP as verified"""
        self.is_otp_verified = True
        self.otp_verified_at = datetime.utcnow()

    def mark_dob_verified(self):
        """Mark DOB as verified and complete verification"""
        self.is_dob_verified = True
        self.dob_verified_at = datetime.utcnow()
        self.is_fully_verified = True
        self.fully_verified_at = datetime.utcnow()

    def __repr__(self):
        return f"<VerificationToken {self.secure_token[:8]}... (Assignment: {self.assignment_id})>"
