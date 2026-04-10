"""
Report Schemas
Pydantic models for report generation, review, and approval
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime


# AI Generation Job Schemas
class JobCreate(BaseModel):
    """Create AI generation job"""
    session_id: UUID
    job_type: str = Field(..., description="Job type: profile, impact, or recommendations")


class JobResponse(BaseModel):
    """AI generation job response"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    session_id: UUID
    job_type: str
    status: str
    output_text: Optional[str] = None
    model_used: Optional[str] = None
    tokens_used: Optional[int] = None
    generation_time_seconds: Optional[float] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


# Report Generation Schemas
class ReportGenerateRequest(BaseModel):
    """Request to generate a new report"""
    session_id: UUID = Field(..., description="Assessment session ID")
    student_id: UUID = Field(..., description="Student ID")


class ReportResponse(BaseModel):
    """Generated report response"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    session_id: UUID
    profile_job_id: Optional[UUID] = None
    impact_job_id: Optional[UUID] = None
    recommendations_job_id: Optional[UUID] = None
    profile_text: Optional[str] = None
    impact_text: Optional[str] = None
    recommendations_text: Optional[str] = None
    status: str
    generated_at: datetime
    created_at: datetime
    updated_at: datetime


# Report Review Schemas
class ReportReviewRequest(BaseModel):
    """Request to review and edit a report"""
    review_status: str = Field(..., description="approved or changes_requested")
    edited_profile_text: Optional[str] = None
    edited_impact_text: Optional[str] = None
    edited_recommendations_text: Optional[str] = None
    reviewer_notes: Optional[str] = None


class ReportReviewResponse(BaseModel):
    """Report review response"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    report_id: UUID
    reviewed_by_user_id: UUID
    review_status: str
    edited_profile_text: Optional[str] = None
    edited_impact_text: Optional[str] = None
    edited_recommendations_text: Optional[str] = None
    reviewer_notes: Optional[str] = None
    reviewed_at: datetime
    created_at: datetime


# Final Report Schemas
class FinalReportResponse(BaseModel):
    """Final report response"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    report_id: UUID
    review_id: Optional[UUID] = None
    pdf_file_path: Optional[str] = None
    docx_file_path: Optional[str] = None
    minio_pdf_key: Optional[str] = None
    minio_docx_key: Optional[str] = None
    report_date: str
    generated_by_user_id: UUID
    approved_by_user_id: Optional[UUID] = None
    status: str
    created_at: datetime
    sent_at: Optional[datetime] = None


# Detailed Report with Jobs
class ReportDetailedResponse(BaseModel):
    """Detailed report response with job information"""
    report: ReportResponse
    profile_job: Optional[JobResponse] = None
    impact_job: Optional[JobResponse] = None
    recommendations_job: Optional[JobResponse] = None
    reviews: list[ReportReviewResponse] = []
