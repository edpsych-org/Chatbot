"""
Admin API Routes
Handles admin-only operations: user management, system monitoring,
student creation, and assignment management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, update, delete as sql_delete
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.security import get_current_active_user, get_password_hash
from app.core.config import settings
from app.models.user import User, UserRole
from app.models.student import Student
from app.models.student_guardian import StudentGuardian
from app.models.assessment import AssessmentSession
from app.models.assignment import AssessmentAssignment, AssignmentStatus
from app.models.magic_link import MagicLinkToken
from app.models.chat import ChatSession, ChatMessage
from app.models.psychologist_report import PsychologistReport
from app.models.upload import IQTestUpload, CognitiveProfile
from app.models.report import GeneratedReport
from app.schemas.user import UserCreate, UserResponse
from app.utils.magic_link import create_invite_magic_link
from app.utils.email import send_assessment_assignment_email


class AdminUserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    organization: Optional[str] = None
    role: Optional[str] = None  # "PARENT", "PSYCHOLOGIST", "SCHOOL", "ADMIN"


class ParentCreate(BaseModel):
    """Parent/Guardian information schema"""
    type: str  # "parent" or "school"
    full_name: str
    email: EmailStr
    phone: str
    relationship: str  # "Mother", "Father", "Guardian", etc.
    is_primary: bool = True


class StudentWithParentCreate(BaseModel):
    """Combined student and parent creation schema"""
    # Student info
    student_first_name: str
    student_last_name: str
    date_of_birth: str  # YYYY-MM-DD
    gender: Optional[str] = None
    grade: Optional[str] = None
    school_name: Optional[str] = None
    medical_history: Optional[str] = None
    notes: Optional[str] = None

    # Parent/Guardian info
    parents: List[ParentCreate]


class AssessmentAssignCreate(BaseModel):
    """Assessment assignment schema"""
    student_id: UUID
    parent_id: UUID
    assessment_type: str = "parent_assessment"
    due_date: Optional[datetime] = None
    notes: Optional[str] = None

router = APIRouter(tags=["admin"])


def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """Dependency to ensure user is admin"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a user with any role (admin only). Used to onboard psychologists."""
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    new_user = User(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
        phone=user_data.phone,
        organization=user_data.organization,
        is_active=True,
        is_verified=True,  # admin-vouched
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


@router.patch("/users/{user_id}")
async def update_user(
    user_id: UUID,
    update_data: AdminUserUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update user fields (admin only)"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Prevent admin from changing their own role away from ADMIN
    if update_data.role and user.id == current_user.id and update_data.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role away from ADMIN",
        )

    if update_data.full_name is not None:
        user.full_name = update_data.full_name
    if update_data.email is not None:
        user.email = update_data.email
    if update_data.phone is not None:
        user.phone = update_data.phone
    if update_data.organization is not None:
        user.organization = update_data.organization
    if update_data.role is not None:
        user.role = UserRole(update_data.role)

    await db.commit()
    await db.refresh(user)

    return {
        "id": str(user.id),
        "email": user.email,
        "role": user.role.value,
        "full_name": user.full_name,
        "phone": user.phone,
        "organization": user.organization,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "created_at": user.created_at.isoformat(),
    }


@router.get("/users")
async def get_all_users(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get all users in the system (admin only)"""
    result = await db.execute(
        select(User).order_by(User.created_at.desc())
    )
    users = result.scalars().all()

    return [
        {
            "id": str(user.id),
            "email": user.email,
            "role": user.role.value,
            "full_name": user.full_name,
            "phone": user.phone,
            "organization": user.organization,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "created_at": user.created_at.isoformat(),
        }
        for user in users
    ]


@router.get("/stats")
async def get_system_stats(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get system-wide statistics (admin only)"""

    # Total users count
    result = await db.execute(select(func.count(User.id)))
    total_users = result.scalar()

    # Total students count
    result = await db.execute(select(func.count(Student.id)))
    total_students = result.scalar()

    # Total assessments count (chat sessions = actual parent assessments)
    result = await db.execute(select(func.count(ChatSession.id)))
    total_assessments = result.scalar()

    # Total reports count (psychologist reports)
    result = await db.execute(select(func.count(PsychologistReport.id)))
    total_reports = result.scalar()

    # Users by role
    users_by_role = {}
    for role in UserRole:
        result = await db.execute(
            select(func.count(User.id)).where(User.role == role)
        )
        users_by_role[role.value] = result.scalar()

    return {
        "total_users": total_users,
        "total_students": total_students,
        "total_assessments": total_assessments,
        "total_reports": total_reports,
        "users_by_role": users_by_role,
    }


@router.patch("/users/{user_id}/toggle-status")
async def toggle_user_status(
    user_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Toggle user active status (admin only)"""

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Don't allow admins to deactivate themselves
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )

    user.is_active = not user.is_active
    await db.commit()
    await db.refresh(user)

    return {"message": f"User {'activated' if user.is_active else 'deactivated'} successfully"}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete a user (admin only)"""

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Don't allow admins to delete themselves
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    # Use raw SQL DELETE so the database ON DELETE CASCADE handles child rows
    # directly, avoiding SQLAlchemy's ORM-level FK nullification which crashes
    # on NOT NULL columns.
    from sqlalchemy import delete as sql_delete
    await db.execute(sql_delete(User).where(User.id == user_id))
    await db.commit()

    return {"message": "User deleted successfully"}


# ---------------------------------------------------------------------------
# Read-only admin data explorer endpoints
# ---------------------------------------------------------------------------


@router.get("/students")
async def admin_list_students(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all students with primary guardian info and chat session counts."""

    # Primary guardian subquery: pick one guardian per student, preferring is_primary="true"
    primary_guardian_rows = await db.execute(
        select(
            StudentGuardian.student_id,
            StudentGuardian.is_primary,
            User.full_name.label("guardian_name"),
            User.email.label("guardian_email"),
        ).join(User, User.id == StudentGuardian.guardian_user_id)
    )
    guardians_by_student: dict = {}
    for row in primary_guardian_rows.all():
        existing = guardians_by_student.get(row.student_id)
        # Prefer primary guardian; otherwise keep first seen
        if existing is None or (row.is_primary == "true" and existing.get("is_primary") != "true"):
            guardians_by_student[row.student_id] = {
                "is_primary": row.is_primary,
                "guardian_name": row.guardian_name,
                "guardian_email": row.guardian_email,
            }

    # Chat session counts per student: chat_sessions -> assignment -> student_id
    count_rows = await db.execute(
        select(
            AssessmentAssignment.student_id,
            func.count(ChatSession.id).label("session_count"),
        )
        .join(ChatSession, ChatSession.assignment_id == AssessmentAssignment.id)
        .group_by(AssessmentAssignment.student_id)
    )
    session_counts = {row.student_id: row.session_count for row in count_rows.all()}

    result = await db.execute(select(Student).order_by(Student.created_at.desc()))
    students = result.scalars().all()

    return [
        {
            "id": str(s.id),
            "first_name": s.first_name,
            "last_name": s.last_name,
            "date_of_birth": s.date_of_birth.isoformat() if s.date_of_birth else None,
            "grade_level": s.year_group,  # model uses `year_group`
            "school_name": s.school_name,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "primary_guardian_name": (guardians_by_student.get(s.id) or {}).get("guardian_name"),
            "primary_guardian_email": (guardians_by_student.get(s.id) or {}).get("guardian_email"),
            "chat_session_count": int(session_counts.get(s.id, 0)),
        }
        for s in students
    ]


@router.get("/chat-sessions")
async def admin_list_chat_sessions(
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all chat sessions (without context_data) with joined student + parent info."""

    stmt = (
        select(
            ChatSession.id,
            ChatSession.status,
            ChatSession.flow_type,
            ChatSession.current_step,
            ChatSession.started_at,
            ChatSession.last_interaction_at,
            ChatSession.completed_at,
            ChatSession.duration_minutes,
            ChatSession.user_id,
            ChatSession.assignment_id,
            Student.first_name.label("student_first_name"),
            Student.last_name.label("student_last_name"),
            User.email.label("parent_email"),
        )
        .join(AssessmentAssignment, AssessmentAssignment.id == ChatSession.assignment_id, isouter=True)
        .join(Student, Student.id == AssessmentAssignment.student_id, isouter=True)
        .join(User, User.id == ChatSession.user_id, isouter=True)
        .order_by(ChatSession.last_interaction_at.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = (await db.execute(stmt)).all()

    return [
        {
            "id": str(r.id),
            "status": r.status,
            "flow_type": r.flow_type,
            "current_step": r.current_step,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "last_interaction_at": r.last_interaction_at.isoformat() if r.last_interaction_at else None,
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            "duration_minutes": r.duration_minutes,
            "user_id": str(r.user_id) if r.user_id else None,
            "assignment_id": str(r.assignment_id) if r.assignment_id else None,
            "student_name": (
                f"{r.student_first_name} {r.student_last_name}"
                if r.student_first_name or r.student_last_name
                else None
            ),
            "parent_email": r.parent_email,
        }
        for r in rows
    ]


@router.get("/chat-sessions/{session_id}")
async def admin_get_chat_session(
    session_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get a single chat session including full context_data JSON."""

    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")

    # Joined student + parent info
    student = None
    if session.assignment_id:
        assign_res = await db.execute(
            select(AssessmentAssignment).where(AssessmentAssignment.id == session.assignment_id)
        )
        assignment = assign_res.scalar_one_or_none()
        if assignment and assignment.student_id:
            stu_res = await db.execute(select(Student).where(Student.id == assignment.student_id))
            student = stu_res.scalar_one_or_none()

    parent = None
    if session.user_id:
        p_res = await db.execute(select(User).where(User.id == session.user_id))
        parent = p_res.scalar_one_or_none()

    return {
        "id": str(session.id),
        "status": session.status,
        "flow_type": session.flow_type,
        "current_step": session.current_step,
        "current_node_id": session.current_node_id,
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "last_interaction_at": session.last_interaction_at.isoformat() if session.last_interaction_at else None,
        "completed_at": session.completed_at.isoformat() if session.completed_at else None,
        "duration_minutes": session.duration_minutes,
        "user_id": str(session.user_id) if session.user_id else None,
        "assignment_id": str(session.assignment_id) if session.assignment_id else None,
        "user_type": session.user_type,
        "context_data": session.context_data or {},
        "student": (
            {
                "id": str(student.id),
                "first_name": student.first_name,
                "last_name": student.last_name,
                "date_of_birth": student.date_of_birth.isoformat() if student.date_of_birth else None,
                "school_name": student.school_name,
                "year_group": student.year_group,
            }
            if student
            else None
        ),
        "parent": (
            {
                "id": str(parent.id),
                "full_name": parent.full_name,
                "email": parent.email,
                "role": parent.role.value,
            }
            if parent
            else None
        ),
    }


@router.get("/psychologist-reports")
async def admin_list_psychologist_reports(
    report_type: str | None = None,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all psychologist reports with content preview and joined student name."""

    stmt = (
        select(
            PsychologistReport.id,
            PsychologistReport.student_id,
            PsychologistReport.report_type,
            PsychologistReport.status,
            PsychologistReport.created_by_user_id,
            PsychologistReport.created_at,
            PsychologistReport.updated_at,
            PsychologistReport.generation_ms,
            PsychologistReport.content_markdown,
            Student.first_name.label("student_first_name"),
            Student.last_name.label("student_last_name"),
        )
        .join(Student, Student.id == PsychologistReport.student_id, isouter=True)
        .order_by(PsychologistReport.updated_at.desc())
    )
    if report_type:
        stmt = stmt.where(PsychologistReport.report_type == report_type)
    stmt = stmt.limit(limit).offset(offset)

    rows = (await db.execute(stmt)).all()

    return [
        {
            "id": str(r.id),
            "student_id": str(r.student_id) if r.student_id else None,
            "report_type": r.report_type,
            "status": r.status,
            "created_by_user_id": str(r.created_by_user_id) if r.created_by_user_id else None,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            "generation_ms": r.generation_ms,
            "content_preview": (r.content_markdown or "")[:300],
            "student_name": (
                f"{r.student_first_name} {r.student_last_name}"
                if r.student_first_name or r.student_last_name
                else None
            ),
        }
        for r in rows
    ]


@router.get("/psychologist-reports/{report_id}")
async def admin_get_psychologist_report(
    report_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get a single psychologist report including full content_markdown and source_data."""

    result = await db.execute(
        select(PsychologistReport).where(PsychologistReport.id == report_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Psychologist report not found"
        )

    student = None
    if report.student_id:
        stu_res = await db.execute(select(Student).where(Student.id == report.student_id))
        student = stu_res.scalar_one_or_none()

    return {
        "id": str(report.id),
        "student_id": str(report.student_id) if report.student_id else None,
        "report_type": report.report_type,
        "status": report.status,
        "created_by_user_id": str(report.created_by_user_id) if report.created_by_user_id else None,
        "created_at": report.created_at.isoformat() if report.created_at else None,
        "updated_at": report.updated_at.isoformat() if report.updated_at else None,
        "generation_ms": report.generation_ms,
        "content_markdown": report.content_markdown or "",
        "source_data": report.source_data,
        "source_chat_session_id": (
            str(report.source_chat_session_id) if report.source_chat_session_id else None
        ),
        "source_cognitive_profile_id": (
            str(report.source_cognitive_profile_id) if report.source_cognitive_profile_id else None
        ),
        "student_name": (
            f"{student.first_name} {student.last_name}" if student else None
        ),
    }


@router.get("/cognitive-profiles")
async def admin_list_cognitive_profiles(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all cognitive profiles with joined student name."""

    stmt = (
        select(
            CognitiveProfile.id,
            CognitiveProfile.student_id,
            CognitiveProfile.test_name,
            CognitiveProfile.test_date,
            CognitiveProfile.confidence_score,
            CognitiveProfile.requires_review,
            CognitiveProfile.parsed_scores,
            CognitiveProfile.raw_ocr_text,
            CognitiveProfile.created_at,
            Student.first_name.label("student_first_name"),
            Student.last_name.label("student_last_name"),
        )
        .join(Student, Student.id == CognitiveProfile.student_id, isouter=True)
        .order_by(CognitiveProfile.created_at.desc())
    )
    rows = (await db.execute(stmt)).all()

    return [
        {
            "id": str(r.id),
            "student_id": str(r.student_id) if r.student_id else None,
            "test_name": r.test_name,
            "test_date": r.test_date.isoformat() if r.test_date else None,
            "confidence_score": r.confidence_score,
            "requires_review": r.requires_review,
            "parsed_scores": r.parsed_scores,
            "raw_ocr_text_length": len(r.raw_ocr_text) if r.raw_ocr_text else 0,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "student_name": (
                f"{r.student_first_name} {r.student_last_name}"
                if r.student_first_name or r.student_last_name
                else None
            ),
        }
        for r in rows
    ]


@router.get("/iq-uploads")
async def admin_list_iq_uploads(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all IQ test upload metadata with joined student + uploader names."""

    uploader = User.__table__.alias("uploader")

    stmt = (
        select(
            IQTestUpload.id,
            IQTestUpload.student_id,
            IQTestUpload.file_name,
            IQTestUpload.file_size_bytes,
            IQTestUpload.uploaded_at,
            IQTestUpload.uploaded_by_user_id,
            IQTestUpload.upload_status,
            Student.first_name.label("student_first_name"),
            Student.last_name.label("student_last_name"),
            uploader.c.full_name.label("uploader_name"),
        )
        .join(Student, Student.id == IQTestUpload.student_id, isouter=True)
        .join(uploader, uploader.c.id == IQTestUpload.uploaded_by_user_id, isouter=True)
        .order_by(IQTestUpload.uploaded_at.desc())
    )
    rows = (await db.execute(stmt)).all()

    return [
        {
            "id": str(r.id),
            "student_id": str(r.student_id) if r.student_id else None,
            "original_filename": r.file_name,  # model uses `file_name`
            "file_size_bytes": r.file_size_bytes,
            "uploaded_at": r.uploaded_at.isoformat() if r.uploaded_at else None,
            "uploaded_by_user_id": str(r.uploaded_by_user_id) if r.uploaded_by_user_id else None,
            "processing_status": (
                r.upload_status.value if hasattr(r.upload_status, "value") else r.upload_status
            ),
            "student_name": (
                f"{r.student_first_name} {r.student_last_name}"
                if r.student_first_name or r.student_last_name
                else None
            ),
            "uploader_name": r.uploader_name,
        }
        for r in rows
    ]


@router.get("/students-with-assessments")
async def admin_list_students_with_assessments(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List students with their latest chat session status."""

    # Get all students with their latest chat session status
    result = await db.execute(select(Student).order_by(Student.created_at.desc()))
    students = result.scalars().all()

    out = []
    for s in students:
        # Find assignments for this student
        assign_result = await db.execute(
            select(AssessmentAssignment).where(AssessmentAssignment.student_id == s.id)
        )
        assignments = assign_result.scalars().all()

        latest_status = None
        session_count = 0
        for assignment in assignments:
            sess_result = await db.execute(
                select(ChatSession)
                .where(ChatSession.assignment_id == assignment.id)
                .order_by(ChatSession.last_interaction_at.desc())
            )
            sessions = sess_result.scalars().all()
            session_count += len(sessions)
            if sessions and latest_status is None:
                latest_status = sessions[0].status

        # Get guardian info
        guard_result = await db.execute(
            select(StudentGuardian.guardian_user_id)
            .where(StudentGuardian.student_id == s.id)
        )
        guardian_ids = [row[0] for row in guard_result.all()]

        guardian_email = None
        if guardian_ids:
            gu_result = await db.execute(
                select(User.email).where(User.id == guardian_ids[0])
            )
            guardian_email = gu_result.scalar_one_or_none()

        out.append({
            "id": str(s.id),
            "first_name": s.first_name,
            "last_name": s.last_name,
            "guardian_email": guardian_email,
            "latest_session_status": latest_status,
            "session_count": session_count,
        })

    return out


@router.post("/students/{student_id}/reset-assessment")
async def reset_student_assessment(
    student_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Reset all assessment chat sessions for a student."""

    # Find all assignments for this student
    result = await db.execute(
        select(AssessmentAssignment).where(AssessmentAssignment.student_id == student_id)
    )
    assignments = result.scalars().all()

    if not assignments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No assessment assignments found for this student",
        )

    sessions_reset = 0
    now = datetime.now(timezone.utc)

    for assignment in assignments:
        sess_result = await db.execute(
            select(ChatSession).where(ChatSession.assignment_id == assignment.id)
        )
        sessions = sess_result.scalars().all()

        for session in sessions:
            # Delete all chat messages for this session
            await db.execute(
                sql_delete(ChatMessage).where(ChatMessage.session_id == session.id)
            )

            # Reset session state
            session.status = "active"
            session.current_step = 0
            session.current_node_id = None
            session.context_data = {}
            session.completed_at = None
            session.duration_minutes = None
            session.last_interaction_at = now

            sessions_reset += 1

    await db.commit()

    return {"message": "Assessment reset successfully", "sessions_reset": sessions_reset}


# ---------------------------------------------------------------------------
# Student creation (moved from psychologist role)
# ---------------------------------------------------------------------------


@router.post("/students/create-with-parents", status_code=status.HTTP_201_CREATED)
async def admin_create_student_with_parents(
    data: StudentWithParentCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Create student + parent/guardians in a single transaction (admin only).

    1. Create a new student profile
    2. Create parent/guardian account(s) or link existing ones
    3. Link parents to student via StudentGuardian
    """

    try:
        # 1. Create student
        student = Student(
            first_name=data.student_first_name,
            last_name=data.student_last_name,
            date_of_birth=datetime.strptime(data.date_of_birth, "%Y-%m-%d").date(),
            gender=data.gender,
            year_group=data.grade,
            school_name=data.school_name,
            created_by_user_id=current_user.id,
        )
        db.add(student)
        await db.flush()  # Get student ID without committing

        created_parents = []

        # 2. Create parent/guardian accounts
        for parent_data in data.parents:
            # Check if user already exists
            existing_user_result = await db.execute(
                select(User).where(User.email == parent_data.email)
            )
            existing_user = existing_user_result.scalar_one_or_none()

            if existing_user:
                parent = existing_user
            else:
                # Create new parent account (no password – will set via magic link)
                parent = User(
                    email=parent_data.email,
                    password_hash=None,
                    role=UserRole.PARENT if parent_data.type == "parent" else UserRole.SCHOOL,
                    full_name=parent_data.full_name,
                    phone=parent_data.phone,
                    is_active=True,
                    is_verified=False,  # Will verify via magic link later
                )
                db.add(parent)
                await db.flush()

                created_parents.append({
                    "email": parent.email,
                    "full_name": parent.full_name,
                })

            # 3. Link parent to student
            guardian_link = StudentGuardian(
                student_id=student.id,
                guardian_user_id=parent.id,
                relationship_type=parent_data.relationship,
                is_primary="true" if parent_data.is_primary else "false",
            )
            db.add(guardian_link)

        await db.commit()
        await db.refresh(student)

        return {
            "success": True,
            "student_id": str(student.id),
            "student_name": f"{student.first_name} {student.last_name}",
            "parents_created": len(created_parents),
            "parents_linked": len(data.parents),
            "message": "Student and parents created successfully",
            "created_parents": created_parents,
        }

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create student and parents: {str(e)}",
        )


# ---------------------------------------------------------------------------
# Assignment management (moved from psychologist role)
# ---------------------------------------------------------------------------


@router.post("/assignments/assign", status_code=status.HTTP_201_CREATED)
async def admin_assign_assessment(
    assignment: AssessmentAssignCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Assign assessment to a parent and generate a secure magic link (admin only).

    1. Create assignment record
    2. Generate secure magic-link token
    3. Send email with link to parent
    4. Return link for admin to share manually if needed
    """

    # Verify student exists
    student_result = await db.execute(
        select(Student).where(Student.id == assignment.student_id)
    )
    student = student_result.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student not found"
        )

    # Verify parent exists
    parent_result = await db.execute(
        select(User).where(User.id == assignment.parent_id)
    )
    parent = parent_result.scalar_one_or_none()
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Parent not found"
        )

    # Check parent-student relationship
    relationship_result = await db.execute(
        select(StudentGuardian).where(
            and_(
                StudentGuardian.student_id == assignment.student_id,
                StudentGuardian.guardian_user_id == assignment.parent_id,
            )
        )
    )
    relationship = relationship_result.scalar_one_or_none()
    if not relationship:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Parent is not linked to this student",
        )

    # Create assignment
    new_assignment = AssessmentAssignment(
        assigned_by_psychologist_id=current_user.id,
        student_id=assignment.student_id,
        assigned_to_user_id=assignment.parent_id,
        status=AssignmentStatus.ASSIGNED,
        due_date=assignment.due_date,
        notes=assignment.notes,
    )
    db.add(new_assignment)
    await db.flush()

    # Create magic link for parent access
    magic_link_token = await create_invite_magic_link(
        db,
        str(new_assignment.assigned_to_user_id),
        str(new_assignment.id),
        expiry_hours=settings.MAGIC_LINK_EXPIRY_HOURS,
    )
    magic_link_url = f"{settings.FRONTEND_URL}/auth/magic/{magic_link_token.token}"

    await db.commit()

    # Send assessment assignment email with magic link
    student_name = f"{student.first_name} {student.last_name}"
    send_assessment_assignment_email(
        parent_email=parent.email,
        parent_name=parent.full_name or parent.email,
        student_name=student_name,
        psychologist_name=current_user.full_name or "Admin",
        assessment_link=magic_link_url,
    )

    return {
        "success": True,
        "assignment_id": str(new_assignment.id),
        "magic_link": magic_link_url,
        "status": "assigned",
        "message": "Assessment assigned and notifications sent",
    }


@router.post("/assignments/{assignment_id}/resend-link")
async def admin_resend_magic_link(
    assignment_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Resend a magic link for an existing assignment (admin only)."""

    # Verify assignment exists
    result = await db.execute(
        select(AssessmentAssignment).where(AssessmentAssignment.id == assignment_id)
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Get assigned parent user
    result = await db.execute(
        select(User).where(User.id == assignment.assigned_to_user_id)
    )
    parent = result.scalar_one_or_none()
    if not parent:
        raise HTTPException(status_code=404, detail="Assigned parent not found")

    # Get student
    result = await db.execute(
        select(Student).where(Student.id == assignment.student_id)
    )
    student = result.scalar_one_or_none()

    # Invalidate existing unused magic links for this assignment
    await db.execute(
        update(MagicLinkToken)
        .where(MagicLinkToken.assignment_id == assignment_id)
        .where(MagicLinkToken.used_at.is_(None))
        .values(used_at=datetime.now(timezone.utc))
    )

    # Create new magic link
    magic_link_token = await create_invite_magic_link(
        db,
        str(parent.id),
        str(assignment.id),
        expiry_hours=settings.MAGIC_LINK_EXPIRY_HOURS,
    )
    magic_link_url = f"{settings.FRONTEND_URL}/auth/magic/{magic_link_token.token}"

    # Send email
    student_name = (
        f"{student.first_name} {student.last_name}" if student else "your child"
    )
    send_assessment_assignment_email(
        parent_email=parent.email,
        parent_name=parent.full_name or parent.email,
        student_name=student_name,
        psychologist_name=current_user.full_name or "Admin",
        assessment_link=magic_link_url,
    )

    return {
        "message": "Magic link resent successfully",
        "magic_link": magic_link_url,
        "sent_to": parent.email,
    }


# ---------------------------------------------------------------------------
# All-students and all-assignments read endpoints (admin only)
# ---------------------------------------------------------------------------


@router.get("/students/all-with-details")
async def admin_get_all_students_with_details(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Return ALL students with guardians, active assignments, and progress (admin only).

    Unlike the psychologist version which filters by created_by_user_id,
    this returns every student in the system.
    """

    result = await db.execute(
        select(Student).order_by(Student.created_at.desc())
    )
    students = result.scalars().all()

    students_with_details = []
    for student in students:
        # Get parents/guardians
        guardians_result = await db.execute(
            select(StudentGuardian, User)
            .join(User, StudentGuardian.guardian_user_id == User.id)
            .where(StudentGuardian.student_id == student.id)
        )
        guardians = guardians_result.all()

        # Get active assignments (non-cancelled)
        assignments_result = await db.execute(
            select(AssessmentAssignment).where(
                and_(
                    AssessmentAssignment.student_id == student.id,
                    AssessmentAssignment.status != AssignmentStatus.CANCELLED,
                )
            )
        )
        assignments = assignments_result.scalars().all()

        # Calculate progress from chat sessions
        progress_pct = 0
        for asgn in assignments:
            if asgn.status in [AssignmentStatus.ASSIGNED, AssignmentStatus.IN_PROGRESS]:
                sess_result = await db.execute(
                    select(ChatSession)
                    .where(ChatSession.assignment_id == asgn.id)
                    .order_by(ChatSession.started_at.desc())
                )
                chat_session = sess_result.scalars().first()
                if chat_session and chat_session.context_data:
                    answered = chat_session.context_data.get("answered_node_ids", [])
                    total_nodes = 102  # parent_assessment_v1 answerable nodes
                    progress_pct = (
                        round((len(answered) / total_nodes) * 100)
                        if total_nodes > 0
                        else 0
                    )
                    if chat_session.status == "completed":
                        progress_pct = 100
                break  # use the first active assignment for progress

        students_with_details.append({
            "id": str(student.id),
            "first_name": student.first_name,
            "last_name": student.last_name,
            "date_of_birth": (
                student.date_of_birth.isoformat() if student.date_of_birth else None
            ),
            "age": (
                (datetime.now().date() - student.date_of_birth).days // 365
                if student.date_of_birth
                else None
            ),
            "gender": student.gender,
            "grade": student.year_group,
            "school_name": student.school_name,
            "created_at": (
                student.created_at.isoformat() if student.created_at else None
            ),
            "guardians": [
                {
                    "id": str(user.id),
                    "name": user.full_name,
                    "email": user.email,
                    "phone": user.phone,
                    "relationship": guardian.relationship_type,
                    "is_primary": guardian.is_primary,
                }
                for guardian, user in guardians
            ],
            "active_assignments": len(assignments),
            "has_active_assessment": any(
                a.status in [AssignmentStatus.ASSIGNED, AssignmentStatus.IN_PROGRESS]
                for a in assignments
            ),
            "progress_percentage": progress_pct,
        })

    return {
        "total": len(students_with_details),
        "students": students_with_details,
    }


@router.get("/assignments/all")
async def admin_get_all_assignments(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Return all assignments with student and assigned_to user info (admin only).
    """

    result = await db.execute(
        select(AssessmentAssignment).order_by(
            AssessmentAssignment.assigned_at.desc()
        )
    )
    assignments = result.scalars().all()

    assignments_with_details = []
    for assignment in assignments:
        # Student info
        student_result = await db.execute(
            select(Student).where(Student.id == assignment.student_id)
        )
        student = student_result.scalar_one_or_none()

        # Assigned-to user info
        assigned_to_result = await db.execute(
            select(User).where(User.id == assignment.assigned_to_user_id)
        )
        assigned_to = assigned_to_result.scalar_one_or_none()

        assignments_with_details.append({
            "id": str(assignment.id),
            "student": (
                {
                    "id": str(student.id),
                    "first_name": student.first_name,
                    "last_name": student.last_name,
                    "grade_level": student.year_group,
                }
                if student
                else None
            ),
            "assigned_to": (
                {
                    "id": str(assigned_to.id),
                    "name": assigned_to.full_name,
                    "email": assigned_to.email,
                    "role": assigned_to.role.value,
                }
                if assigned_to
                else None
            ),
            "status": (
                assignment.status.value
                if hasattr(assignment.status, "value")
                else str(assignment.status)
            ),
            "notes": assignment.notes,
            "due_date": (
                assignment.due_date.isoformat() if assignment.due_date else None
            ),
            "assigned_at": assignment.assigned_at.isoformat(),
        })

    return assignments_with_details


@router.patch("/assignments/{assignment_id}/cancel")
async def admin_cancel_assignment(
    assignment_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Cancel an assessment assignment (admin only).
    Sets status to CANCELLED. Cannot cancel already-completed assignments.
    """

    result = await db.execute(
        select(AssessmentAssignment).where(AssessmentAssignment.id == assignment_id)
    )
    assignment = result.scalar_one_or_none()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )

    if assignment.status == AssignmentStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel a completed assignment",
        )

    assignment.status = AssignmentStatus.CANCELLED
    await db.commit()

    return {"message": "Assignment cancelled successfully"}
