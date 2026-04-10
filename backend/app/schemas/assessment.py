"""
Assessment Session Pydantic Schemas
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

from app.models.assessment import SessionStatus, QuestionType


class SessionCreate(BaseModel):
    """Schema for starting a new assessment session"""
    student_id: UUID


class SessionResponse(BaseModel):
    """Schema for assessment session response"""
    id: UUID
    student_id: UUID
    parent_id: UUID
    status: SessionStatus
    progress_percentage: int
    current_section: Optional[str] = None
    resume_token: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class QuestionResponse(BaseModel):
    """Schema for chatbot question"""
    id: UUID
    question_number: int
    section: str
    question_text: str
    question_type: QuestionType
    options: Optional[Dict[str, Any]] = None
    is_required: bool
    help_text: Optional[str] = None
    order_index: int

    class Config:
        from_attributes = True


class AnswerSubmit(BaseModel):
    """Schema for submitting an answer"""
    session_token: str
    question_id: UUID
    answer_text: Optional[str] = None
    answer_data: Optional[Dict[str, Any]] = None


class AnswerResponse(BaseModel):
    """Schema for answer response"""
    id: UUID
    session_id: UUID
    question_id: UUID
    answer_text: Optional[str] = None
    answer_data: Optional[Dict[str, Any]] = None
    is_complete: bool
    answered_at: datetime

    class Config:
        from_attributes = True


class SessionProgressResponse(BaseModel):
    """Schema for session progress"""
    session: SessionResponse
    total_questions: int
    answered_questions: int
    progress_percentage: int
    next_question: Optional[QuestionResponse] = None
