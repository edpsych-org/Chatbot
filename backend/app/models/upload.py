"""
Upload and Cognitive Profile Models
IQ test uploads and parsed cognitive data
"""

from sqlalchemy import Column, String, BigInteger, Date, Text, Boolean, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base


class UploadStatus(str, enum.Enum):
    """File upload status"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class IQTestUpload(Base):
    __tablename__ = "iq_test_uploads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    uploaded_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=False)
    mime_type = Column(String(100))
    minio_bucket = Column(String(100))
    minio_object_key = Column(String(500))
    upload_status = Column(SQLEnum(UploadStatus), default=UploadStatus.UPLOADED, index=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True))

    # Relationships
    student = relationship("Student", backref="iq_test_uploads")
    uploaded_by = relationship("User", backref="iq_test_uploads", passive_deletes=True)

    def __repr__(self):
        return f"<IQTestUpload {self.file_name} - {self.upload_status}>"


class CognitiveProfile(Base):
    __tablename__ = "cognitive_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    iq_test_upload_id = Column(UUID(as_uuid=True), ForeignKey("iq_test_uploads.id", ondelete="SET NULL"), index=True)
    test_name = Column(String(100), nullable=False)  # WISC-V, WIAT-III, etc.
    test_date = Column(Date)
    administered_by = Column(String(255))
    raw_ocr_text = Column(Text)
    parsed_scores = Column(JSONB, nullable=False)  # Structured test scores
    percentiles = Column(JSONB)
    confidence_score = Column(Float)  # OCR/parsing confidence
    requires_review = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    student = relationship("Student", backref="cognitive_profiles")
    iq_test_upload = relationship("IQTestUpload", backref="cognitive_profiles")

    def __repr__(self):
        return f"<CognitiveProfile {self.test_name} for student={self.student_id}>"
