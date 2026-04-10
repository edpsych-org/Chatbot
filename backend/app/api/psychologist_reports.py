"""
Psychologist Reports Workspace API

Endpoints to power the per-student Reports Workspace:
  - Generate a background summary from the latest completed parent chat session.
  - Upload an IQ test PDF, extract text + structured scores, persist a CognitiveProfile.
  - Generate a cognitive report from the latest CognitiveProfile.
  - Synthesize unified insights from the latest background + cognitive reports.
  - CRUD-style edit/finalize endpoints for any PsychologistReport row.
"""

import logging
import os
import time
import uuid as uuid_lib
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Response
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User, UserRole
from app.models.student import Student
from app.models.chat import ChatSession, ChatSessionStatus
from app.models.upload import IQTestUpload, UploadStatus, CognitiveProfile
from app.models.psychologist_report import PsychologistReport
from app.agents.report_agents import (
    BackgroundSummaryAgent,
    IQScoreExtractorAgent,
    CognitiveReportAgent,
    UnifiedInsightsAgent,
)
from app.services.pdf_extractor import extract_text_from_pdf

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/psychologist-reports", tags=["psychologist-reports"])


# Ensure temp upload directory exists once at import time.
TEMP_UPLOAD_DIR = "/tmp/iq_uploads"
try:
    os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)
except Exception as e:
    logger.warning(f"Could not create {TEMP_UPLOAD_DIR}: {e}")


# ============================================================================
# AUTH DEPENDENCY
# ============================================================================
def require_psychologist_or_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Only psychologists and admins may access the reports workspace."""
    if current_user.role not in [UserRole.PSYCHOLOGIST, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Psychologist or Admin access required",
        )
    return current_user


# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================
class ReportOut(BaseModel):
    id: str
    student_id: str
    report_type: str
    content_markdown: str
    status: str
    source_chat_session_id: Optional[str] = None
    source_cognitive_profile_id: Optional[str] = None
    generation_ms: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class BlankReportCreate(BaseModel):
    report_type: str  # "background_summary" | "cognitive_report" | "unified_insights"


class ReportUpdate(BaseModel):
    content_markdown: str


# ============================================================================
# HELPERS
# ============================================================================
def _serialize_report(r: PsychologistReport) -> dict:
    return {
        "id": str(r.id),
        "student_id": str(r.student_id),
        "created_by_user_id": str(r.created_by_user_id) if r.created_by_user_id else None,
        "report_type": r.report_type,
        "content_markdown": r.content_markdown or "",
        "source_data": r.source_data,
        "source_chat_session_id": str(r.source_chat_session_id) if r.source_chat_session_id else None,
        "source_cognitive_profile_id": str(r.source_cognitive_profile_id) if r.source_cognitive_profile_id else None,
        "status": r.status,
        "generation_ms": r.generation_ms,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
    }


def _serialize_profile(p: CognitiveProfile, upload: Optional[IQTestUpload] = None) -> dict:
    return {
        "id": str(p.id),
        "student_id": str(p.student_id),
        "iq_test_upload_id": str(p.iq_test_upload_id) if p.iq_test_upload_id else None,
        "test_name": p.test_name,
        "test_date": p.test_date.isoformat() if p.test_date else None,
        "administered_by": p.administered_by,
        "parsed_scores": p.parsed_scores,
        "raw_ocr_text": p.raw_ocr_text,
        "confidence_score": p.confidence_score,
        "requires_review": p.requires_review,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        "iq_test_upload": {
            "id": str(upload.id),
            "file_name": upload.file_name,
            "file_size_bytes": upload.file_size_bytes,
            "mime_type": upload.mime_type,
            "uploaded_at": upload.uploaded_at.isoformat() if upload.uploaded_at else None,
        } if upload else None,
    }


async def _get_student_or_404(db: AsyncSession, student_id: uuid_lib.UUID) -> Student:
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


async def _get_report_or_404(db: AsyncSession, report_id: uuid_lib.UUID) -> PsychologistReport:
    result = await db.execute(
        select(PsychologistReport).where(PsychologistReport.id == report_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


async def _latest_completed_session(
    db: AsyncSession, student_id: uuid_lib.UUID
) -> Optional[ChatSession]:
    """Find the most recent COMPLETED ChatSession for this student."""
    # Chat sessions are linked to students via the assignment_id foreign key.
    from app.models.assignment import AssessmentAssignment

    result = await db.execute(
        select(ChatSession)
        .join(AssessmentAssignment, ChatSession.assignment_id == AssessmentAssignment.id)
        .where(AssessmentAssignment.student_id == student_id)
        .where(ChatSession.status == ChatSessionStatus.COMPLETED.value)
        .order_by(desc(ChatSession.id))
    )
    return result.scalars().first()


async def _latest_report(
    db: AsyncSession, student_id: uuid_lib.UUID, report_type: str
) -> Optional[PsychologistReport]:
    result = await db.execute(
        select(PsychologistReport)
        .where(PsychologistReport.student_id == student_id)
        .where(PsychologistReport.report_type == report_type)
        .order_by(desc(PsychologistReport.created_at))
    )
    return result.scalars().first()


# ============================================================================
# GET WORKSPACE STATE
# ============================================================================
@router.get("/students/{student_id}/workspace")
async def get_workspace(
    student_id: uuid_lib.UUID,
    current_user: User = Depends(require_psychologist_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Return all state needed to render the Reports Workspace for a student:
      - the student record
      - the latest completed ChatSession's context_data (if any)
      - every existing PsychologistReport, grouped by report_type (latest first)
      - every CognitiveProfile row with its IQTestUpload metadata
    """
    student = await _get_student_or_404(db, student_id)

    latest_session = await _latest_completed_session(db, student_id)

    # All reports for this student, newest first
    reports_result = await db.execute(
        select(PsychologistReport)
        .where(PsychologistReport.student_id == student_id)
        .order_by(desc(PsychologistReport.created_at))
    )
    all_reports = reports_result.scalars().all()

    grouped_reports = {
        "background_summary": [],
        "cognitive_report": [],
        "unified_insights": [],
    }
    for r in all_reports:
        grouped_reports.setdefault(r.report_type, []).append(_serialize_report(r))

    # Cognitive profiles (+ their uploads)
    profiles_result = await db.execute(
        select(CognitiveProfile)
        .where(CognitiveProfile.student_id == student_id)
        .order_by(desc(CognitiveProfile.created_at))
    )
    profiles = profiles_result.scalars().all()

    profile_dicts = []
    for p in profiles:
        upload = None
        if p.iq_test_upload_id:
            upload_result = await db.execute(
                select(IQTestUpload).where(IQTestUpload.id == p.iq_test_upload_id)
            )
            upload = upload_result.scalar_one_or_none()
        profile_dicts.append(_serialize_profile(p, upload))

    return {
        "student": {
            "id": str(student.id),
            "first_name": student.first_name,
            "last_name": student.last_name,
            "date_of_birth": student.date_of_birth.isoformat() if student.date_of_birth else None,
            "year_group": student.year_group,
            "school_name": student.school_name,
        },
        "latest_completed_session": {
            "id": str(latest_session.id),
            "context_data": latest_session.context_data,
            "status": latest_session.status,
        } if latest_session else None,
        "reports": grouped_reports,
        "cognitive_profiles": profile_dicts,
    }


# ============================================================================
# BACKGROUND SUMMARY — GENERATE
# ============================================================================
@router.post("/students/{student_id}/background-summary/generate")
async def generate_background_summary(
    student_id: uuid_lib.UUID,
    current_user: User = Depends(require_psychologist_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Generate a Background Summary from the student's latest completed parent chat session."""
    student = await _get_student_or_404(db, student_id)

    session = await _latest_completed_session(db, student_id)
    if not session:
        raise HTTPException(
            status_code=400,
            detail="No completed parent assessment session found for this student. "
                   "The parent must finish their assessment before a background summary can be generated.",
        )

    context_data = session.context_data or {}
    student_name = f"{student.first_name} {student.last_name}".strip() or "the student"

    agent = BackgroundSummaryAgent()
    started = time.time()
    try:
        markdown = await agent.generate(context_data, student_name)
    except Exception as e:
        logger.error(f"BackgroundSummaryAgent raised: {e}", exc_info=True)
        raise HTTPException(status_code=502, detail=f"Agent failed: {str(e)}")
    generation_ms = int((time.time() - started) * 1000)

    report = PsychologistReport(
        student_id=student_id,
        created_by_user_id=current_user.id,
        report_type="background_summary",
        content_markdown=markdown,
        source_data={"chat_session_context": context_data},
        source_chat_session_id=session.id,
        status="draft",
        generation_ms=generation_ms,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    return _serialize_report(report)


# ============================================================================
# COGNITIVE REPORT — UPLOAD PDF
# ============================================================================
@router.post("/students/{student_id}/cognitive-report/upload")
async def upload_cognitive_report_pdf(
    student_id: uuid_lib.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(require_psychologist_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Accept an IQ test PDF/image, extract text (text-layer or OCR),
    call the IQScoreExtractorAgent, and persist IQTestUpload + CognitiveProfile.
    The uploaded file itself is DELETED after extraction — only the extracted
    text + structured scores persist in the database.
    """
    await _get_student_or_404(db, student_id)

    allowed_mimes = {
        "application/pdf",
        "image/png",
        "image/jpeg",
        "image/jpg",
    }
    if file.content_type not in allowed_mimes:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{file.content_type}'. Must be PDF, PNG, or JPEG.",
        )

    file_bytes = await file.read()
    size = len(file_bytes)
    if size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File exceeds 10 MB limit.")
    if size == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Persist to temp path for debugging / inspection mid-pipeline; deleted in finally.
    temp_id = uuid_lib.uuid4()
    ext = ".pdf" if file.content_type == "application/pdf" else (
        ".png" if file.content_type == "image/png" else ".jpg"
    )
    temp_path = os.path.join(TEMP_UPLOAD_DIR, f"{temp_id}{ext}")

    try:
        try:
            os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)
            with open(temp_path, "wb") as f:
                f.write(file_bytes)
        except Exception as e:
            logger.warning(f"Failed to persist temp upload to {temp_path}: {e}")

        # 1. Extract text (text layer → OCR fallback)
        try:
            raw_text, confidence, ocr_used = extract_text_from_pdf(file_bytes)
        except Exception as e:
            logger.error(f"pdf extraction failed: {e}", exc_info=True)
            raise HTTPException(status_code=422, detail=f"Failed to read file: {str(e)}")

        if not raw_text or len(raw_text.strip()) < 20:
            raise HTTPException(
                status_code=422,
                detail="Could not extract readable text from the uploaded file. "
                       "If this is a scanned document, the OCR engine may have failed.",
            )

        # 2. Run the extractor agent
        agent = IQScoreExtractorAgent()
        try:
            parsed = await agent.extract(raw_text)
        except Exception as e:
            logger.error(f"IQScoreExtractorAgent failed: {e}", exc_info=True)
            raise HTTPException(status_code=502, detail=f"Score extraction failed: {str(e)}")

        if isinstance(parsed, dict) and parsed.get("error"):
            raise HTTPException(status_code=422, detail=parsed["error"])

        # 3. Create IQTestUpload row (file_path stored for provenance even though file is deleted)
        iq_upload = IQTestUpload(
            student_id=student_id,
            uploaded_by_user_id=current_user.id,
            file_name=file.filename or f"upload{ext}",
            file_path=temp_path,
            file_size_bytes=size,
            mime_type=file.content_type,
            upload_status=UploadStatus.COMPLETED,
        )
        db.add(iq_upload)
        await db.flush()

        # 4. Create CognitiveProfile row
        test_name = parsed.get("test_name") if isinstance(parsed, dict) else None
        profile = CognitiveProfile(
            student_id=student_id,
            iq_test_upload_id=iq_upload.id,
            test_name=test_name or "Unknown cognitive assessment",
            administered_by=parsed.get("administered_by") if isinstance(parsed, dict) else None,
            raw_ocr_text=raw_text,
            parsed_scores=parsed,
            confidence_score=confidence,
            requires_review=confidence < 0.9,
        )
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
        await db.refresh(iq_upload)

        return {
            "ocr_used": ocr_used,
            "confidence_score": confidence,
            "cognitive_profile": _serialize_profile(profile, iq_upload),
        }

    finally:
        # Always delete the temp file — privacy: no raw PDFs retained.
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception as e:
            logger.warning(f"Failed to delete temp file {temp_path}: {e}")


# ============================================================================
# COGNITIVE REPORT — GENERATE NARRATIVE
# ============================================================================
@router.post("/students/{student_id}/cognitive-report/generate")
async def generate_cognitive_report(
    student_id: uuid_lib.UUID,
    current_user: User = Depends(require_psychologist_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Generate a narrative Cognitive Report from the latest CognitiveProfile."""
    student = await _get_student_or_404(db, student_id)

    result = await db.execute(
        select(CognitiveProfile)
        .where(CognitiveProfile.student_id == student_id)
        .order_by(desc(CognitiveProfile.created_at))
    )
    profile = result.scalars().first()
    if not profile:
        raise HTTPException(
            status_code=400,
            detail="No cognitive profile found for this student. Upload an IQ test PDF first.",
        )

    student_name = f"{student.first_name} {student.last_name}".strip() or "the student"

    agent = CognitiveReportAgent()
    started = time.time()
    try:
        markdown = await agent.generate(profile.parsed_scores or {}, student_name)
    except Exception as e:
        logger.error(f"CognitiveReportAgent raised: {e}", exc_info=True)
        raise HTTPException(status_code=502, detail=f"Agent failed: {str(e)}")
    generation_ms = int((time.time() - started) * 1000)

    report = PsychologistReport(
        student_id=student_id,
        created_by_user_id=current_user.id,
        report_type="cognitive_report",
        content_markdown=markdown,
        source_data={"parsed_scores": profile.parsed_scores},
        source_cognitive_profile_id=profile.id,
        status="draft",
        generation_ms=generation_ms,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    return _serialize_report(report)


# ============================================================================
# UNIFIED INSIGHTS — GENERATE
# ============================================================================
@router.post("/students/{student_id}/unified-insights/generate")
async def generate_unified_insights(
    student_id: uuid_lib.UUID,
    current_user: User = Depends(require_psychologist_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Generate a cross-reference Unified Insights report from latest background + cognitive reports."""
    student = await _get_student_or_404(db, student_id)

    background = await _latest_report(db, student_id, "background_summary")
    cognitive = await _latest_report(db, student_id, "cognitive_report")

    if not background or not cognitive:
        missing = []
        if not background:
            missing.append("background summary")
        if not cognitive:
            missing.append("cognitive report")
        raise HTTPException(
            status_code=400,
            detail=f"Both a background summary and a cognitive report are required. Missing: {', '.join(missing)}.",
        )

    student_name = f"{student.first_name} {student.last_name}".strip() or "the student"

    agent = UnifiedInsightsAgent()
    started = time.time()
    try:
        markdown = await agent.synthesize(
            background.content_markdown or "",
            cognitive.content_markdown or "",
            student_name,
        )
    except Exception as e:
        logger.error(f"UnifiedInsightsAgent raised: {e}", exc_info=True)
        raise HTTPException(status_code=502, detail=f"Agent failed: {str(e)}")
    generation_ms = int((time.time() - started) * 1000)

    report = PsychologistReport(
        student_id=student_id,
        created_by_user_id=current_user.id,
        report_type="unified_insights",
        content_markdown=markdown,
        source_data={
            "background_summary_id": str(background.id),
            "cognitive_report_id": str(cognitive.id),
        },
        source_chat_session_id=background.source_chat_session_id,
        source_cognitive_profile_id=cognitive.source_cognitive_profile_id,
        status="draft",
        generation_ms=generation_ms,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    return _serialize_report(report)


# ============================================================================
# BLANK REPORT — create empty editable row
# ============================================================================
@router.post("/students/{student_id}/reports/blank")
async def create_blank_report(
    student_id: uuid_lib.UUID,
    payload: BlankReportCreate,
    current_user: User = Depends(require_psychologist_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create an empty editable report (used by the 'Start blank' flow)."""
    await _get_student_or_404(db, student_id)

    allowed_types = {"background_summary", "cognitive_report", "unified_insights"}
    if payload.report_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid report_type '{payload.report_type}'. Must be one of {sorted(allowed_types)}.",
        )

    report = PsychologistReport(
        student_id=student_id,
        created_by_user_id=current_user.id,
        report_type=payload.report_type,
        content_markdown="",
        status="draft",
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    return _serialize_report(report)


# ============================================================================
# REPORT CRUD — patch / delete / finalize
# ============================================================================
@router.patch("/reports/{report_id}")
async def update_report(
    report_id: uuid_lib.UUID,
    payload: ReportUpdate,
    current_user: User = Depends(require_psychologist_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update the markdown content of an existing report (autosave + manual save)."""
    report = await _get_report_or_404(db, report_id)
    report.content_markdown = payload.content_markdown
    # updated_at is updated automatically via onupdate=func.now()
    await db.commit()
    await db.refresh(report)
    return _serialize_report(report)


@router.delete("/reports/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: uuid_lib.UUID,
    current_user: User = Depends(require_psychologist_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete a report row (used by 'Discard and regenerate')."""
    report = await _get_report_or_404(db, report_id)
    await db.delete(report)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/reports/{report_id}/finalize")
async def finalize_report(
    report_id: uuid_lib.UUID,
    current_user: User = Depends(require_psychologist_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Lock a report: status -> 'final'."""
    report = await _get_report_or_404(db, report_id)
    report.status = "final"
    await db.commit()
    await db.refresh(report)
    return _serialize_report(report)
