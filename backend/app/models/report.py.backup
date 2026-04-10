"""
Report Models
AI generation jobs, generated reports, reviews, and final reports
"""

from sqlalchemy import Column, String, Integer, Text, Float, Date, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base


class JobType(str, enum.Enum):
    """AI generation job types"""
    PROFILE = "profile"
    IMPACT = "impact"
    RECOMMENDATIONS = "recommendations"


class JobStatus(str, enum.Enum):
    """Job execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ReportStatus(str, enum.Enum):
    """Generated report status"""
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    REJECTED = "rejected"


class ReviewStatus(str, enum.Enum):
    """Review status"""
    PENDING = "pending"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"


class FinalReportStatus(str, enum.Enum):
    """Final report status"""
    GENERATED = "generated"
    SENT = "sent"
    ARCHIVED = "archived"


class AIGenerationJob(Base):
    __tablename__ = "ai_generation_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("assessment_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    job_type = Column(SQLEnum(JobType), nullable=False, index=True)
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING, index=True)
    input_data = Column(JSONB, nullable=False)
    output_text = Column(Text)
    model_used = Column(String(100))
    tokens_used = Column(Integer)
    generation_time_seconds = Column(Float)
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

    # Relationships
    student = relationship("Student", backref="ai_generation_jobs")
    session = relationship("AssessmentSession", backref="ai_generation_jobs")

    def __repr__(self):
        return f"<AIGenerationJob {self.job_type} - {self.status}>"


class GeneratedReport(Base):
    __tablename__ = "generated_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("assessment_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    profile_job_id = Column(UUID(as_uuid=True), ForeignKey("ai_generation_jobs.id"))
    impact_job_id = Column(UUID(as_uuid=True), ForeignKey("ai_generation_jobs.id"))
    recommendations_job_id = Column(UUID(as_uuid=True), ForeignKey("ai_generation_jobs.id"))
    profile_text = Column(Text)
    impact_text = Column(Text)
    recommendations_text = Column(Text)
    status = Column(SQLEnum(ReportStatus), default=ReportStatus.DRAFT, index=True)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    student = relationship("Student", backref="generated_reports")
    session = relationship("AssessmentSession", backref="generated_reports")
    profile_job = relationship("AIGenerationJob", foreign_keys=[profile_job_id])
    impact_job = relationship("AIGenerationJob", foreign_keys=[impact_job_id])
    recommendations_job = relationship("AIGenerationJob", foreign_keys=[recommendations_job_id])

    def __repr__(self):
        return f"<GeneratedReport {self.id} - {self.status}>"


class ReportReview(Base):
    __tablename__ = "report_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id = Column(UUID(as_uuid=True), ForeignKey("generated_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewed_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    review_status = Column(SQLEnum(ReviewStatus), nullable=False, index=True)
    edited_profile_text = Column(Text)
    edited_impact_text = Column(Text)
    edited_recommendations_text = Column(Text)
    reviewer_notes = Column(Text)
    reviewed_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    report = relationship("GeneratedReport", backref="reviews")
    reviewed_by = relationship("User", backref="report_reviews")

    def __repr__(self):
        return f"<ReportReview {self.id} - {self.review_status}>"


class FinalReport(Base):
    __tablename__ = "final_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    report_id = Column(UUID(as_uuid=True), ForeignKey("generated_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    review_id = Column(UUID(as_uuid=True), ForeignKey("report_reviews.id", ondelete="SET NULL"))
    pdf_file_path = Column(String(500))
    docx_file_path = Column(String(500))
    minio_pdf_key = Column(String(500))
    minio_docx_key = Column(String(500))
    report_date = Column(Date, nullable=False)
    generated_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    approved_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    status = Column(SQLEnum(FinalReportStatus), default=FinalReportStatus.GENERATED, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    sent_at = Column(DateTime(timezone=True))

    # Relationships
    student = relationship("Student", backref="final_reports")
    report = relationship("GeneratedReport", backref="final_reports")
    review = relationship("ReportReview", backref="final_reports")
    generated_by = relationship("User", foreign_keys=[generated_by_user_id], backref="generated_final_reports")
    approved_by = relationship("User", foreign_keys=[approved_by_user_id], backref="approved_final_reports")

    def __repr__(self):
        return f"<FinalReport {self.id} - {self.status}>"
