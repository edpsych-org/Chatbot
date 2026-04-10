"""
Student-Guardian Relationship Model
Maps which parents/guardians have authority over which students
Supports multiple guardians per student and multiple students per guardian
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class StudentGuardian(Base):
    """
    Association table for student-guardian relationships

    This enables:
    - One student can have multiple guardians (mother, father, etc.)
    - One guardian (parent/school) can have multiple students
    - Proper validation when assigning assessments
    """
    __tablename__ = "student_guardians"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    guardian_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    relationship_type = Column(String(50), nullable=True)  # e.g., "Mother", "Father", "Guardian", "School"
    is_primary = Column(String(10), default="false")  # "true" or "false" as string for primary contact
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    student = relationship("Student", backref="guardians")
    guardian = relationship("User", foreign_keys=[guardian_user_id], backref="students_under_care", passive_deletes=True)
    created_by = relationship("User", foreign_keys=[created_by_user_id])

    # Ensure a guardian can only be linked to a student once
    __table_args__ = (
        UniqueConstraint('student_id', 'guardian_user_id', name='unique_student_guardian'),
    )

    def __repr__(self):
        return f"<StudentGuardian student_id={self.student_id} guardian_id={self.guardian_user_id}>"
