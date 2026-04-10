"""
Hybrid Chat Models
Chat sessions, messages, and conversation context for AI-powered assessments
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base


class ChatSessionStatus(str, enum.Enum):
    """Chat session status"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class MessageRole(str, enum.Enum):
    """Message sender role"""
    USER = "user"
    BOT = "bot"
    SYSTEM = "system"


class MessageType(str, enum.Enum):
    """Type of message"""
    TEXT = "text"
    MCQ_CHOICE = "mcq_choice"
    ADAPTIVE_QUESTION = "adaptive_question"
    CLARIFICATION = "clarification"
    SUMMARY = "summary"


class ChatSession(Base):
    """
    Chat session for hybrid assessment
    Links to existing assessment assignment
    """
    __tablename__ = "chat_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Link to assessment assignment
    assignment_id = Column(UUID(as_uuid=True), ForeignKey("assessment_assignments.id", ondelete="CASCADE"), nullable=False)

    # User info
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user_type = Column(String(50), nullable=False)  # "parent" | "teacher"

    # Session state
    status = Column(String(50), nullable=False, default=ChatSessionStatus.ACTIVE.value)
    flow_type = Column(String(100), nullable=False)  # "parent_assessment" | "teacher_assessment"
    current_step = Column(Integer, default=0)
    current_node_id = Column(String(100))

    # Context data (all session state) - MutableDict enables in-place change detection
    context_data = Column(MutableDict.as_mutable(JSONB), default={})
    """
    Structure:
    {
        "user_profile": {
            "student_name": "John",
            "student_age": 9,
            "grade": "4th"
        },
        "assessment_data": {
            "attention": {
                "severity": "medium",
                "indicators": ["homework", "classroom"],
                "mcq_answers": {"attention_1": "sometimes"},
                "text_inputs": ["gets distracted during homework"],
                "ai_insights": ["Shows moderate attention challenges in structured settings"]
            },
            "social": {...},
            "emotional": {...},
            "academic": {...},
            "behavioral": {...}
        },
        "conversation_summary": "Parent reports moderate attention issues...",
        "explored_areas": ["attention", "social"],
        "pending_areas": ["emotional", "academic"],
        "adaptive_questions_asked": 3,
        "total_messages": 15
    }
    """

    # Metadata
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    last_interaction_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))
    duration_minutes = Column(Integer)

    # Relationships
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    assignment = relationship("AssessmentAssignment")
    user = relationship("User")

    def __repr__(self):
        return f"<ChatSession {self.id} - {self.flow_type} ({self.status})>"


class ChatMessage(Base):
    """
    Individual chat message in a session
    Stores both user and bot messages with metadata
    """
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)

    # Message info
    role = Column(String(50), nullable=False)  # "user" | "bot" | "system"
    message_type = Column(String(50), nullable=False)  # MessageType enum
    content = Column(Text, nullable=False)

    # Metadata (question data, options, etc.)
    message_metadata = Column("metadata", JSONB, default={})
    """
    For BOT messages:
    {
        "question_id": "attention_1",
        "category": "attention",
        "options": [
            {"value": "yes", "label": "Yes, often"},
            {"value": "no", "label": "Rarely/Never"}
        ],
        "allow_text": true,
        "flow_node_id": "attention_1"
    }

    For USER messages:
    {
        "selected_option": "yes",
        "question_id": "attention_1",
        "is_mcq": true
    }
    """

    # AI analysis (for text messages)
    intent_classification = Column(JSONB)
    """
    {
        "category": "attention",
        "severity": "medium",
        "entities": ["homework", "classroom"],
        "confidence": 0.85,
        "keywords": ["distracted", "focus"],
        "sentiment": "concerned"
    }
    """

    # Generation info (for bot messages)
    generation_source = Column(String(50))  # "flow_engine" | "ai_adaptive" | "ai_empathetic"
    generation_metadata = Column(JSONB)  # Prompt used, model, etc.

    # Timing
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("ChatSession", back_populates="messages")

    def __repr__(self):
        return f"<ChatMessage {self.role}: {self.content[:50]}...>"


class FlowDefinition(Base):
    """
    Flow definitions stored in database
    Allows dynamic flow updates without code changes
    """
    __tablename__ = "flow_definitions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    flow_id = Column(String(100), unique=True, nullable=False)  # e.g., "parent_attention_v1"
    flow_name = Column(String(255), nullable=False)
    flow_type = Column(String(50), nullable=False)  # "parent" | "teacher"
    category = Column(String(50))  # "attention" | "social" | etc.

    # Flow configuration (JSON)
    flow_data = Column(JSONB, nullable=False)
    """
    Complete flow structure as per architecture doc
    """

    # Versioning
    version = Column(String(20), nullable=False)
    is_active = Column(Boolean, default=True)

    # Metadata
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<FlowDefinition {self.flow_id} v{self.version}>"


class ConversationTemplate(Base):
    """
    Reusable conversation templates for AI
    """
    __tablename__ = "conversation_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    template_type = Column(String(50), nullable=False)  # "empathetic_response" | "clarification" | "summary"
    category = Column(String(50))  # "attention" | "social" | etc.
    scenario = Column(String(255))  # "parent_concern" | "unclear_input" | etc.

    # Template content
    prompt_template = Column(Text, nullable=False)
    example_output = Column(Text)

    # Metadata
    is_active = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<ConversationTemplate {self.template_type}>"
