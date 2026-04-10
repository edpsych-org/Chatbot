"""
Psychologist API Routes
Comprehensive workflow for psychologists including:
- Student + Parent creation (single flow)
- Assessment assignment with secure links
- IQ report upload and processing
- Report review and approval
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr
from app.core.database import get_db
from app.core.security import get_current_active_user, get_password_hash
from app.core.config import settings
from app.models.user import User, UserRole
from app.models.student import Student
from app.models.student_guardian import StudentGuardian
from app.models.assignment import AssessmentAssignment, AssignmentStatus
from app.models.upload import IQTestUpload, UploadStatus, CognitiveProfile
from app.models.chat import ChatSession
from app.models.report import GeneratedReport, ReportStatus, FinalReport, FinalReportStatus
from app.utils.magic_link import create_invite_magic_link
from app.utils.email import send_assessment_assignment_email

router = APIRouter(prefix="/psychologist", tags=["psychologist"])


# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================

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


class ReportApprovalRequest(BaseModel):
    """Report approval schema"""
    psychologist_notes: Optional[str] = None
    approved: bool = True


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def require_psychologist_or_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """Dependency to ensure user is psychologist or admin"""
    if current_user.role not in [UserRole.PSYCHOLOGIST, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Psychologist or Admin access required"
        )
    return current_user


# ============================================================================
# STUDENT + PARENT CREATION (SINGLE FLOW)
# ============================================================================

@router.post("/students/create-with-parents", status_code=status.HTTP_201_CREATED)
async def create_student_with_parents(
    data: StudentWithParentCreate,
    current_user: User = Depends(require_psychologist_or_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Create student + parent/guardians in single transaction

    NO dropdowns - all manual entry

    This is the MAIN entry point for psychologists to:
    1. Create a new student profile
    2. Create parent/guardian account(s)
    3. Link parents to student
    4. Generate secure credentials
    5. Send welcome notifications
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
            created_by_user_id=current_user.id
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
                # Link existing user to student
                parent = existing_user
            else:
                # Create new parent account (no password - will set via magic link)
                parent = User(
                    email=parent_data.email,
                    password_hash=None,
                    role=UserRole.PARENT if parent_data.type == "parent" else UserRole.SCHOOL,
                    full_name=parent_data.full_name,
                    phone=parent_data.phone,
                    is_active=True,
                    is_verified=False  # Will verify via magic link later
                )
                db.add(parent)
                await db.flush()

                created_parents.append({
                    "email": parent.email,
                    "full_name": parent.full_name
                })

            # 3. Link parent to student
            guardian_link = StudentGuardian(
                student_id=student.id,
                guardian_user_id=parent.id,
                relationship_type=parent_data.relationship,
                is_primary="true" if parent_data.is_primary else "false"
            )
            db.add(guardian_link)

        await db.commit()
        await db.refresh(student)

        # 4. TODO: Send welcome emails to new parents
        # for parent_info in created_parents:
        #     await send_welcome_email(
        #         email=parent_info["email"],
        #         password=parent_info["temporary_password"],
        #         student_name=f"{student.first_name} {student.last_name}"
        #     )

        return {
            "success": True,
            "student_id": str(student.id),
            "student_name": f"{student.first_name} {student.last_name}",
            "parents_created": len(created_parents),
            "parents_linked": len(data.parents),
            "message": "Student and parents created successfully",
            "created_parents": created_parents
        }

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create student and parents: {str(e)}"
        )


# ============================================================================
# ASSESSMENT ASSIGNMENT WITH SECURE LINK
# ============================================================================

@router.post("/assignments/assign", status_code=status.HTTP_201_CREATED)
async def assign_assessment_with_secure_link(
    assignment: AssessmentAssignCreate,
    current_user: User = Depends(require_psychologist_or_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Assign assessment to parent and generate secure link with OTP

    Workflow:
    1. Create assignment
    2. Generate secure token (32-byte URL-safe)
    3. Generate 6-digit OTP
    4. Send email + SMS with link and OTP
    5. Return link for psychologist to share
    """

    # Verify student exists
    student_result = await db.execute(
        select(Student).where(Student.id == assignment.student_id)
    )
    student = student_result.scalar_one_or_none()
    if not student:
        raise HTTPException(404, "Student not found")

    # Verify parent exists and is linked to student
    parent_result = await db.execute(
        select(User).where(User.id == assignment.parent_id)
    )
    parent = parent_result.scalar_one_or_none()
    if not parent:
        raise HTTPException(404, "Parent not found")

    # Check parent-student relationship
    relationship_result = await db.execute(
        select(StudentGuardian).where(
            and_(
                StudentGuardian.student_id == assignment.student_id,
                StudentGuardian.guardian_user_id == assignment.parent_id
            )
        )
    )
    relationship = relationship_result.scalar_one_or_none()
    if not relationship:
        raise HTTPException(403, "Parent is not linked to this student")

    # Create assignment
    new_assignment = AssessmentAssignment(
        assigned_by_psychologist_id=current_user.id,
        student_id=assignment.student_id,
        assigned_to_user_id=assignment.parent_id,
        status=AssignmentStatus.ASSIGNED,
        due_date=assignment.due_date,
        notes=assignment.notes
    )
    db.add(new_assignment)
    await db.flush()

    # Create magic link for parent access
    magic_link_token = await create_invite_magic_link(
        db, str(new_assignment.assigned_to_user_id), str(new_assignment.id),
        expiry_hours=settings.MAGIC_LINK_EXPIRY_HOURS
    )
    magic_link_url = f"{settings.FRONTEND_URL}/auth/magic/{magic_link_token.token}"

    await db.commit()

    # Send assessment assignment email with magic link
    student_name = f"{student.first_name} {student.last_name}"
    send_assessment_assignment_email(
        parent_email=parent.email,
        parent_name=parent.full_name or parent.email,
        student_name=student_name,
        psychologist_name=current_user.full_name or "Your Psychologist",
        assessment_link=magic_link_url
    )

    return {
        "success": True,
        "assignment_id": str(new_assignment.id),
        "magic_link": magic_link_url,
        "status": "assigned",
        "message": "Assessment assigned and notifications sent"
    }


# ============================================================================
# RESEND MAGIC LINK FOR ASSIGNMENT
# ============================================================================

@router.post("/assignments/{assignment_id}/resend-link")
async def resend_magic_link(
    assignment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_psychologist_or_admin)
):
    """Resend a magic link for an existing assignment."""
    from app.models.assignment import AssessmentAssignment
    from app.models.magic_link import MagicLinkToken
    from app.utils.magic_link import create_invite_magic_link
    from app.utils.email import send_assessment_assignment_email
    from datetime import datetime, timezone

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
    from app.models.student import Student
    result = await db.execute(
        select(Student).where(Student.id == assignment.student_id)
    )
    student = result.scalar_one_or_none()

    # Invalidate existing unused magic links for this assignment
    from sqlalchemy import update
    await db.execute(
        update(MagicLinkToken)
        .where(MagicLinkToken.assignment_id == assignment_id)
        .where(MagicLinkToken.used_at.is_(None))
        .values(used_at=datetime.now(timezone.utc))
    )

    # Create new magic link
    magic_link_token = await create_invite_magic_link(
        db, str(parent.id), str(assignment.id),
        expiry_hours=settings.MAGIC_LINK_EXPIRY_HOURS
    )
    magic_link_url = f"{settings.FRONTEND_URL}/auth/magic/{magic_link_token.token}"

    # Send email
    student_name = f"{student.first_name} {student.last_name}" if student else "your child"
    send_assessment_assignment_email(
        parent_email=parent.email,
        parent_name=parent.full_name or parent.email,
        student_name=student_name,
        psychologist_name=current_user.full_name or "Your Psychologist",
        assessment_link=magic_link_url
    )

    return {
        "message": "Magic link resent successfully",
        "magic_link": magic_link_url,
        "sent_to": parent.email
    }


# ============================================================================
# GET ALL STUDENTS FOR PSYCHOLOGIST
# ============================================================================

@router.get("/students/my-students")
async def get_my_students(
    current_user: User = Depends(require_psychologist_or_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all students created by this psychologist with parent information
    """

    # Get students created by this psychologist
    result = await db.execute(
        select(Student)
        .where(Student.created_by_user_id == current_user.id)
        .order_by(Student.created_at.desc())
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

        # Get active assignments
        assignments_result = await db.execute(
            select(AssessmentAssignment)
            .where(
                and_(
                    AssessmentAssignment.student_id == student.id,
                    AssessmentAssignment.status != AssignmentStatus.CANCELLED
                )
            )
        )
        assignments = assignments_result.scalars().all()

        students_with_details.append({
            "id": str(student.id),
            "first_name": student.first_name,
            "last_name": student.last_name,
            "date_of_birth": student.date_of_birth.isoformat() if student.date_of_birth else None,
            "age": (datetime.now().date() - student.date_of_birth).days // 365 if student.date_of_birth else None,
            "gender": student.gender,
            "grade": student.year_group,
            "school_name": student.school_name,
            "created_at": student.created_at.isoformat() if student.created_at else None,
            "guardians": [
                {
                    "id": str(user.id),
                    "name": user.full_name,
                    "email": user.email,
                    "phone": user.phone,
                    "relationship": guardian.relationship_type,
                    "is_primary": guardian.is_primary
                }
                for guardian, user in guardians
            ],
            "active_assignments": len(assignments),
            "has_active_assessment": any(
                a.status in [AssignmentStatus.ASSIGNED, AssignmentStatus.IN_PROGRESS]
                for a in assignments
            )
        })

    return {
        "total": len(students_with_details),
        "students": students_with_details
    }


# ============================================================================
# GET ALL STUDENTS (READ-ONLY FOR PSYCHOLOGIST)
# ============================================================================

@router.get("/students/all-students")
async def get_all_students_readonly(
    current_user: User = Depends(require_psychologist_or_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get ALL students with parent info and assignment progress (read-only view).
    Used by psychologist dashboard to see student list without creation rights.
    """
    result = await db.execute(
        select(Student).order_by(Student.created_at.desc())
    )
    students = result.scalars().all()

    students_with_details = []
    for student in students:
        # Get primary guardian
        guardians_result = await db.execute(
            select(StudentGuardian, User)
            .join(User, StudentGuardian.guardian_user_id == User.id)
            .where(StudentGuardian.student_id == student.id)
        )
        guardians = guardians_result.all()

        primary_guardian = None
        for guardian, user in guardians:
            if guardian.is_primary == "true" or primary_guardian is None:
                primary_guardian = {
                    "name": user.full_name,
                    "email": user.email,
                    "relationship": guardian.relationship_type,
                }

        # Get assignment status and progress
        assignments_result = await db.execute(
            select(AssessmentAssignment)
            .where(
                and_(
                    AssessmentAssignment.student_id == student.id,
                    AssessmentAssignment.status != AssignmentStatus.CANCELLED
                )
            )
        )
        assignments = assignments_result.scalars().all()

        assignment_status = None
        progress_percentage = 0
        for a in assignments:
            if a.status in [AssignmentStatus.ASSIGNED, AssignmentStatus.IN_PROGRESS]:
                assignment_status = a.status.value if hasattr(a.status, 'value') else str(a.status)
                # Get progress from chat session
                sess_result = await db.execute(
                    select(ChatSession)
                    .where(ChatSession.assignment_id == a.id)
                    .order_by(ChatSession.last_interaction_at.desc())
                )
                session = sess_result.scalars().first()
                if session and session.context_data:
                    answered = session.context_data.get("answered_node_ids", [])
                    from app.api.hybrid_chat import flow_engine
                    progress_percentage = flow_engine.calculate_progress(
                        session.flow_type, answered
                    )
                break
            elif a.status == AssignmentStatus.COMPLETED:
                assignment_status = "completed"
                progress_percentage = 100

        students_with_details.append({
            "id": str(student.id),
            "first_name": student.first_name,
            "last_name": student.last_name,
            "grade": student.year_group,
            "school_name": student.school_name,
            "parent": primary_guardian,
            "assignment_status": assignment_status,
            "progress_percentage": progress_percentage,
            "has_active_assignment": any(
                a.status in [AssignmentStatus.ASSIGNED, AssignmentStatus.IN_PROGRESS]
                for a in assignments
            ),
        })

    return {
        "total": len(students_with_details),
        "students": students_with_details
    }


# ============================================================================
# IQ REPORT UPLOAD PLACEHOLDER
# ============================================================================

@router.post("/iq-reports/upload")
async def upload_iq_report(
    student_id: UUID,
    file: UploadFile = File(...),
    test_date: str = Form(...),
    test_type: str = Form(...),
    notes: Optional[str] = Form(None),
    current_user: User = Depends(require_psychologist_or_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload IQ test report (PDF/Image)

    TODO: Implement full IQ processing pipeline
    - File storage (MinIO/S3)
    - OCR extraction
    - LLM analysis
    - Cognitive profile generation
    """

    # Validate file type
    allowed_types = ["application/pdf", "image/jpeg", "image/png"]
    if file.content_type not in allowed_types:
        raise HTTPException(400, "Only PDF, JPG, PNG files are supported")

    # TODO: Save file to storage
    # file_key = f"iq-reports/{student_id}/{uuid.uuid4()}.{file.filename.split('.')[-1]}"
    # await storage.upload_file(file_key, file.file)

    return {
        "success": True,
        "message": "IQ report upload endpoint - implementation in progress",
        "file_name": file.filename,
        "file_size": file.size,
        "student_id": str(student_id)
    }


# ============================================================================
# DASHBOARD STATISTICS
# ============================================================================

@router.get("/dashboard/stats")
async def get_psychologist_dashboard_stats(
    current_user: User = Depends(require_psychologist_or_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get dashboard statistics for psychologist
    """

    # Count students
    students_result = await db.execute(
        select(Student).where(Student.created_by_user_id == current_user.id)
    )
    total_students = len(students_result.scalars().all())

    # Count active assignments
    assignments_result = await db.execute(
        select(AssessmentAssignment).where(
            and_(
                AssessmentAssignment.assigned_by_psychologist_id == current_user.id,
                AssessmentAssignment.status.in_([
                    AssignmentStatus.ASSIGNED,
                    AssignmentStatus.IN_PROGRESS
                ])
            )
        )
    )
    active_assignments = len(assignments_result.scalars().all())

    # Count pending reports
    # TODO: Query generated reports pending review
    pending_reports = 0

    return {
        "total_students": total_students,
        "active_assignments": active_assignments,
        "pending_reports": pending_reports,
        "completed_this_month": 0  # TODO: Calculate
    }
