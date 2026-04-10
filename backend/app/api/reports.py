"""
Reports API Routes
AI generation, review, and export
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List, Optional
from uuid import UUID
from datetime import datetime, date
import logging

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User, UserRole
from app.models.student import Student
from app.models.student_guardian import StudentGuardian
from app.models.assessment import AssessmentSession, ChatbotAnswer, ChatbotQuestion
from app.models.report import (
    AIGenerationJob, GeneratedReport, ReportReview, FinalReport
)
from app.schemas.report import (
    ReportGenerateRequest, ReportResponse, ReportDetailedResponse,
    JobResponse, ReportReviewRequest, ReportReviewResponse,
    FinalReportResponse
)
from app.services.local_llm import llm_service

router = APIRouter()
logger = logging.getLogger(__name__)


async def generate_report_section_bg(
    job_id: UUID,
    job_type: str,
    chatbot_data: dict,
    db: AsyncSession
):
    """Background task to generate report section using LLM"""
    try:
        # Get the job
        result = await db.execute(
            select(AIGenerationJob).where(AIGenerationJob.id == job_id)
        )
        job = result.scalar_one_or_none()

        if not job:
            logger.error(f"Job {job_id} not found")
            return

        # Update job status to running
        job.status = 'running'
        await db.commit()

        # Generate content based on job type
        start_time = datetime.now()

        if job_type == 'profile':
            result = llm_service.generate_profile_section(chatbot_data)
        elif job_type == 'impact':
            result = llm_service.generate_impact_section(chatbot_data)
        elif job_type == 'recommendations':
            result = llm_service.generate_recommendations_section(chatbot_data)
        else:
            raise ValueError(f"Unknown job type: {job_type}")

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Update job with results
        if result.get("success"):
            job.status = 'completed'
            job.output_text = result.get("text", "")
            job.model_used = result.get("model", "qwen2.5:7b")
            job.tokens_used = result.get("tokens", 0)
            job.generation_time_seconds = duration
            job.completed_at = end_time
        else:
            job.status = 'failed'
            job.error_message = result.get("error", "Unknown error")
            job.completed_at = end_time

        await db.commit()
        logger.info(f"Job {job_id} completed with status: {job.status}")

    except Exception as e:
        logger.error(f"Error in background job {job_id}: {e}")
        if job:
            job.status = 'failed'
            job.error_message = str(e)
            job.completed_at = datetime.now()
            await db.commit()


@router.post("/generate", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def generate_report(
    request: ReportGenerateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate AI report for a completed assessment session
    Creates 3 background jobs: Profile, Impact, and Recommendations
    """
    # Verify session exists and belongs to user
    result = await db.execute(
        select(AssessmentSession).where(
            and_(
                AssessmentSession.id == request.session_id,
                AssessmentSession.parent_id == current_user.id
            )
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or access denied"
        )

    # Verify session is completed
    if session.status not in ['COMPLETED', 'SUBMITTED']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only generate reports for completed sessions"
        )

    # Check if report already exists for this session
    result = await db.execute(
        select(GeneratedReport).where(GeneratedReport.session_id == request.session_id)
    )
    existing_report = result.scalar_one_or_none()

    if existing_report:
        return existing_report

    # Get student information
    result = await db.execute(
        select(Student).where(Student.id == request.student_id)
    )
    student = result.scalar_one_or_none()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )

    # Get all chatbot answers for this session
    result = await db.execute(
        select(ChatbotAnswer, ChatbotQuestion).join(
            ChatbotQuestion, ChatbotAnswer.question_id == ChatbotQuestion.id
        ).where(ChatbotAnswer.session_id == request.session_id)
    )
    answers = result.all()

    # Prepare chatbot data for LLM
    chatbot_data = {
        "student_name": f"{student.first_name} {student.last_name}",
        "age": (date.today() - student.date_of_birth).days // 365 if student.date_of_birth else "unknown",
        "school": student.school_name or "not specified",
        "year_group": student.year_group or "not specified",
        "answers": {}
    }

    # Organize answers by section
    for answer, question in answers:
        section = question.section
        if section not in chatbot_data["answers"]:
            chatbot_data["answers"][section] = []

        chatbot_data["answers"][section].append({
            "question": question.question_text,
            "answer_data": answer.answer_data,
            "answer_text": answer.answer_text
        })

    # Extract common concerns from chatbot data
    chatbot_data["concerns"] = "Assessment completed via chatbot questionnaire"
    chatbot_data["family_background"] = "Information gathered via parent questionnaire"
    chatbot_data["learning_difficulties"] = str(chatbot_data["answers"].get("Academic", []))
    chatbot_data["classroom_behavior"] = str(chatbot_data["answers"].get("Behavioral", []))
    chatbot_data["identified_needs"] = f"Based on assessment responses across {len(chatbot_data['answers'])} areas"
    chatbot_data["current_support"] = "To be determined from assessment"

    # Create the report record
    new_report = GeneratedReport(
        student_id=request.student_id,
        session_id=request.session_id,
        status='draft'
    )
    db.add(new_report)
    await db.commit()
    await db.refresh(new_report)

    # Create 3 AI generation jobs
    job_types = ['profile', 'impact', 'recommendations']
    jobs = {}

    for job_type in job_types:
        new_job = AIGenerationJob(
            student_id=request.student_id,
            session_id=request.session_id,
            job_type=job_type,
            status='pending',
            input_data=chatbot_data
        )
        db.add(new_job)
        await db.commit()
        await db.refresh(new_job)

        jobs[job_type] = new_job.id

        # Schedule background generation
        background_tasks.add_task(
            generate_report_section_bg,
            new_job.id,
            job_type,
            chatbot_data,
            db
        )

    # Update report with job IDs
    new_report.profile_job_id = jobs['profile']
    new_report.impact_job_id = jobs['impact']
    new_report.recommendations_job_id = jobs['recommendations']
    await db.commit()
    await db.refresh(new_report)

    logger.info(f"Report generation started for session {request.session_id}")

    return new_report


@router.get("/{report_id}", response_model=ReportDetailedResponse)
async def get_report(
    report_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get generated report with job details"""
    # Get report
    result = await db.execute(
        select(GeneratedReport).where(GeneratedReport.id == report_id)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    # Verify access (user must be the parent of the student or a psychologist)
    result = await db.execute(
        select(Student).where(
            and_(
                Student.id == report.student_id,
                or_(
                    Student.created_by_user_id == current_user.id,
                    current_user.role == 'psychologist'
                )
            )
        )
    )
    student = result.scalar_one_or_none()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Get all jobs
    profile_job = None
    impact_job = None
    recommendations_job = None

    if report.profile_job_id:
        result = await db.execute(
            select(AIGenerationJob).where(AIGenerationJob.id == report.profile_job_id)
        )
        profile_job = result.scalar_one_or_none()

        # Update report with completed job text
        if profile_job and profile_job.status == 'completed' and not report.profile_text:
            report.profile_text = profile_job.output_text
            await db.commit()

    if report.impact_job_id:
        result = await db.execute(
            select(AIGenerationJob).where(AIGenerationJob.id == report.impact_job_id)
        )
        impact_job = result.scalar_one_or_none()

        if impact_job and impact_job.status == 'completed' and not report.impact_text:
            report.impact_text = impact_job.output_text
            await db.commit()

    if report.recommendations_job_id:
        result = await db.execute(
            select(AIGenerationJob).where(AIGenerationJob.id == report.recommendations_job_id)
        )
        recommendations_job = result.scalar_one_or_none()

        if recommendations_job and recommendations_job.status == 'completed' and not report.recommendations_text:
            report.recommendations_text = recommendations_job.output_text
            await db.commit()

    # Get reviews
    result = await db.execute(
        select(ReportReview).where(ReportReview.report_id == report_id).order_by(ReportReview.reviewed_at.desc())
    )
    reviews = result.scalars().all()

    # Check if all jobs are completed and update report status
    if (profile_job and profile_job.status == 'completed' and
        impact_job and impact_job.status == 'completed' and
        recommendations_job and recommendations_job.status == 'completed' and
        report.status == 'draft'):
        report.status = 'review'
        await db.commit()

    return ReportDetailedResponse(
        report=report,
        profile_job=profile_job,
        impact_job=impact_job,
        recommendations_job=recommendations_job,
        reviews=reviews
    )


@router.patch("/{report_id}/review", response_model=ReportReviewResponse)
async def review_report(
    report_id: UUID,
    review_data: ReportReviewRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Psychologist review and edit report"""
    # Only psychologists can review
    if current_user.role != 'psychologist':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only psychologists can review reports"
        )

    # Get report
    result = await db.execute(
        select(GeneratedReport).where(GeneratedReport.id == report_id)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    # Create review record
    new_review = ReportReview(
        report_id=report_id,
        reviewed_by_user_id=current_user.id,
        review_status=review_data.review_status,
        edited_profile_text=review_data.edited_profile_text,
        edited_impact_text=review_data.edited_impact_text,
        edited_recommendations_text=review_data.edited_recommendations_text,
        reviewer_notes=review_data.reviewer_notes
    )

    db.add(new_review)

    # Update report status
    if review_data.review_status == 'approved':
        report.status = 'approved'

        # If edited texts provided, update report
        if review_data.edited_profile_text:
            report.profile_text = review_data.edited_profile_text
        if review_data.edited_impact_text:
            report.impact_text = review_data.edited_impact_text
        if review_data.edited_recommendations_text:
            report.recommendations_text = review_data.edited_recommendations_text
    elif review_data.review_status == 'changes_requested':
        report.status = 'review'

    await db.commit()
    await db.refresh(new_review)

    return new_review


@router.post("/{report_id}/approve", response_model=FinalReportResponse, status_code=status.HTTP_201_CREATED)
async def approve_report(
    report_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Approve a report for final generation (creates final report record)"""
    # Only psychologists can approve
    if current_user.role != 'psychologist':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only psychologists can approve reports"
        )

    # Get report
    result = await db.execute(
        select(GeneratedReport).where(GeneratedReport.id == report_id)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    if report.status != 'approved':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Report must be reviewed and approved first"
        )

    # Check if final report already exists
    result = await db.execute(
        select(FinalReport).where(FinalReport.report_id == report_id)
    )
    existing_final = result.scalar_one_or_none()

    if existing_final:
        return existing_final

    # Get the latest approved review
    result = await db.execute(
        select(ReportReview).where(
            and_(
                ReportReview.report_id == report_id,
                ReportReview.review_status == 'approved'
            )
        ).order_by(ReportReview.reviewed_at.desc()).limit(1)
    )
    latest_review = result.scalar_one_or_none()

    # Create final report record
    final_report = FinalReport(
        student_id=report.student_id,
        report_id=report_id,
        review_id=latest_review.id if latest_review else None,
        report_date=date.today(),
        generated_by_user_id=current_user.id,
        approved_by_user_id=current_user.id,
        status='generated'
    )

    db.add(final_report)
    await db.commit()
    await db.refresh(final_report)

    logger.info(f"Final report {final_report.id} created for report {report_id}")

    return final_report


@router.post("/{report_id}/export")
async def export_report(
    report_id: UUID,
    format: str = "pdf",
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Export report to PDF/DOCX (stub - requires document generation library)"""
    # Get final report
    result = await db.execute(
        select(FinalReport).where(FinalReport.report_id == report_id)
    )
    final_report = result.scalar_one_or_none()

    if not final_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Final report not found. Please approve the report first."
        )

    # TODO: Implement actual PDF/DOCX generation using reportlab or python-docx
    # This would generate the document and upload to MinIO

    return {
        "message": f"Export to {format} not yet implemented",
        "final_report_id": final_report.id,
        "status": "stub"
    }


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(
    job_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get AI generation job status"""
    result = await db.execute(
        select(AIGenerationJob).where(AIGenerationJob.id == job_id)
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    # Verify access
    result = await db.execute(
        select(Student).where(
            and_(
                Student.id == job.student_id,
                or_(
                    Student.created_by_user_id == current_user.id,
                    current_user.role == 'psychologist'
                )
            )
        )
    )
    student = result.scalar_one_or_none()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    return job


# ============================================================================
# PARENT REPORTS ENDPOINT
# ============================================================================

@router.get("/parent/my-reports")
async def get_parent_reports(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all approved/generated reports for students linked to this parent.
    Finds students via two paths:
      1. StudentGuardian link table (guardian_user_id)
      2. Students created by this user (created_by_user_id)
    Returns reports with student info for each.
    """
    if current_user.role not in (UserRole.PARENT, UserRole.PARENT.value, "PARENT"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can access this endpoint"
        )

    # Path 1: Students linked via StudentGuardian
    result = await db.execute(
        select(StudentGuardian.student_id).where(
            StudentGuardian.guardian_user_id == current_user.id
        )
    )
    guardian_student_ids = [row[0] for row in result.all()]

    # Path 2: Students created by this user
    result = await db.execute(
        select(Student.id).where(Student.created_by_user_id == current_user.id)
    )
    created_student_ids = [row[0] for row in result.all()]

    # Combine and deduplicate
    all_student_ids = list(set(guardian_student_ids + created_student_ids))

    if not all_student_ids:
        return []

    # Get all reports for those students that are approved or in review
    result = await db.execute(
        select(GeneratedReport).where(
            GeneratedReport.student_id.in_(all_student_ids)
        ).order_by(GeneratedReport.created_at.desc())
    )
    reports = result.scalars().all()

    # Fetch student info for all relevant students
    result = await db.execute(
        select(Student).where(Student.id.in_(all_student_ids))
    )
    students = {str(s.id): s for s in result.scalars().all()}

    # Build response
    response = []
    for report in reports:
        student = students.get(str(report.student_id))
        response.append({
            "report_id": str(report.id),
            "student_id": str(report.student_id),
            "student_name": f"{student.first_name} {student.last_name}" if student else "Unknown",
            "student_year_group": student.year_group if student else None,
            "student_school": student.school_name if student else None,
            "status": report.status.value if hasattr(report.status, 'value') else str(report.status),
            "has_profile": bool(report.profile_text),
            "has_impact": bool(report.impact_text),
            "has_recommendations": bool(report.recommendations_text),
            "generated_at": report.generated_at.isoformat() if report.generated_at else None,
            "created_at": report.created_at.isoformat() if report.created_at else None,
            "updated_at": report.updated_at.isoformat() if report.updated_at else None,
        })

    return response


# ============================================================================
# PSYCHOLOGIST REPORTS ENDPOINT
# ============================================================================

@router.get("/psychologist/all")
async def get_psychologist_reports(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by report status: draft, review, approved, rejected"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all reports (psychologist has access to all).
    Includes student info, status, and dates.
    Optional status filter via query parameter.
    """
    if current_user.role not in (UserRole.PSYCHOLOGIST, UserRole.PSYCHOLOGIST.value, "PSYCHOLOGIST"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only psychologists can access this endpoint"
        )

    # Build query
    query = select(GeneratedReport)
    if status_filter:
        query = query.where(GeneratedReport.status == status_filter)
    query = query.order_by(GeneratedReport.created_at.desc())

    result = await db.execute(query)
    reports = result.scalars().all()

    if not reports:
        return []

    # Gather all student IDs
    student_ids = list(set(r.student_id for r in reports))

    # Fetch student info
    result = await db.execute(
        select(Student).where(Student.id.in_(student_ids))
    )
    students = {str(s.id): s for s in result.scalars().all()}

    # Build response
    response = []
    for report in reports:
        student = students.get(str(report.student_id))
        response.append({
            "report_id": str(report.id),
            "session_id": str(report.session_id),
            "student_id": str(report.student_id),
            "student_name": f"{student.first_name} {student.last_name}" if student else "Unknown",
            "student_year_group": student.year_group if student else None,
            "student_school": student.school_name if student else None,
            "status": report.status.value if hasattr(report.status, 'value') else str(report.status),
            "has_profile": bool(report.profile_text),
            "has_impact": bool(report.impact_text),
            "has_recommendations": bool(report.recommendations_text),
            "profile_job_id": str(report.profile_job_id) if report.profile_job_id else None,
            "impact_job_id": str(report.impact_job_id) if report.impact_job_id else None,
            "recommendations_job_id": str(report.recommendations_job_id) if report.recommendations_job_id else None,
            "generated_at": report.generated_at.isoformat() if report.generated_at else None,
            "created_at": report.created_at.isoformat() if report.created_at else None,
            "updated_at": report.updated_at.isoformat() if report.updated_at else None,
        })

    return response
