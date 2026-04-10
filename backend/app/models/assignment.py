"""
Assessment Assignment Model
Tracks which assessments have been assigned to which students by psychologists
"""

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base


class AssignmentStatus(str, enum.Enum):
    """Status of assessment assignment"""
    ASSIGNED = "ASSIGNED"           # Assigned but not started
    IN_PROGRESS = "IN_PROGRESS"     # Assessment started
    COMPLETED = "COMPLETED"         # Assessment completed
    CANCELLED = "CANCELLED"         # Assignment cancelled


class AssessmentAssignment(Base):
    """
    Represents an assessment assigned to a student by a psychologist
    """
    __tablename__ = "assessment_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Who assigned this assessment
    assigned_by_psychologist_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # Which student should take the assessment
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False, index=True)

    # Who should complete it (parent or school)
    assigned_to_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # Optional: Link to the actual assessment session once started
    assessment_session_id = Column(UUID(as_uuid=True), ForeignKey("assessment_sessions.id"), nullable=True)

    # Status tracking
    status = Column(SQLEnum(AssignmentStatus), default=AssignmentStatus.ASSIGNED, nullable=False, index=True)

    # Optional notes from psychologist
    notes = Column(Text, nullable=True)

    # Due date (optional)
    due_date = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    assigned_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    psychologist = relationship("User", foreign_keys=[assigned_by_psychologist_id])
    assigned_to_user = relationship("User", foreign_keys=[assigned_to_user_id])
    student = relationship("Student", backref="assessment_assignments")
    assessment_session = relationship("AssessmentSession", backref="assignment")
    verification_token = relationship("VerificationToken", back_populates="assignment", uselist=False)

    def __repr__(self):
        return f"<AssessmentAssignment {self.id} - Student {self.student_id} - Status {self.status}>"
