"""
Psychologist Report Model
Editable AI-drafted reports (background summary, cognitive report, unified insights)
"""

from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class PsychologistReport(Base):
    """
    An editable report draft authored (or AI-drafted) by a psychologist for a student.

    report_type is one of:
      - "background_summary"  (narrative derived from parent chat session context_data)
      - "cognitive_report"    (narrative derived from a CognitiveProfile / IQ PDF upload)
      - "unified_insights"    (cross-reference of the two above)
    """

    __tablename__ = "psychologist_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    report_type = Column(String(30), nullable=False, index=True)
    content_markdown = Column(Text, nullable=False, default="")
    source_data = Column(JSONB, nullable=True)  # snapshot of inputs used for generation
    source_chat_session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="SET NULL"),
        nullable=True,
    )
    source_cognitive_profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("cognitive_profiles.id", ondelete="SET NULL"),
        nullable=True,
    )
    status = Column(String(20), nullable=False, default="draft")  # generating | draft | final
    generation_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    student = relationship("Student", backref="psychologist_reports")
    created_by = relationship("User", backref="authored_psychologist_reports", passive_deletes=True)

    def __repr__(self):
        return f"<PsychologistReport {self.report_type} student={self.student_id} status={self.status}>"
