"""
Student Pydantic Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from uuid import UUID


class StudentCreate(BaseModel):
    """Schema for creating a student"""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: date
    gender: Optional[str] = None
    school_name: Optional[str] = None
    year_group: Optional[str] = None


class StudentUpdate(BaseModel):
    """Schema for updating student info"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[str] = None
    school_name: Optional[str] = None
    year_group: Optional[str] = None


class StudentResponse(BaseModel):
    """Schema for student in API responses"""
    id: UUID
    first_name: str
    last_name: str
    date_of_birth: date
    gender: Optional[str] = None
    school_name: Optional[str] = None
    year_group: Optional[str] = None
    created_by_user_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
