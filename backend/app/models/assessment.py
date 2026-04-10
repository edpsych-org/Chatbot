"""
Assessment Models
Chatbot sessions, questions, and answers
"""

from sqlalchemy import Column, String, Integer, Text, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base


class SessionStatus(str, enum.Enum):
    """Assessment session status"""
    DRAFT = "DRAFT"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    SUBMITTED = "SUBMITTED"


class QuestionType(str, enum.Enum):
    """Question types for chatbot"""
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    TEXT = "TEXT"
    YES_NO = "YES_NO"
    SCALE = "SCALE"


class AssessmentSession(Base):
    __tablename__ = "assessment_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    # Use String instead of SQLEnum to work with VARCHAR column type
    status = Column(String(50), nullable=False, default='DRAFT', index=True)
    progress_percentage = Column(Integer, default=0)
    current_section = Column(String(100))
    resume_token = Column(String(255), unique=True, index=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    submitted_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    student = relationship("Student", backref="assessment_sessions")
    parent = relationship("User", backref="assessment_sessions", passive_deletes=True)

    def __repr__(self):
        return f"<AssessmentSession {self.id} - {self.status}>"


class ChatbotQuestion(Base):
    __tablename__ = "chatbot_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_number = Column(Integer, unique=True, nullable=False)
    section = Column(String(100), nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    # Use String instead of SQLEnum to work with VARCHAR column type
    question_type = Column(String(50), nullable=False)
    options = Column(JSONB)  # For MCQ options
    is_required = Column(Boolean, default=True)
    help_text = Column(Text)
    order_index = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<ChatbotQuestion {self.question_number}: {self.question_text[:50]}>"


class ChatbotAnswer(Base):
    __tablename__ = "chatbot_answers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("assessment_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(UUID(as_uuid=True), ForeignKey("chatbot_questions.id", ondelete="CASCADE"), nullable=False, index=True)
    answer_text = Column(Text)
    answer_data = Column(JSONB)  # For structured answers
    is_complete = Column(Boolean, default=False)
    answered_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    session = relationship("AssessmentSession", backref="answers")
    question = relationship("ChatbotQuestion", backref="answers")

    def __repr__(self):
        return f"<ChatbotAnswer session={self.session_id}>"
