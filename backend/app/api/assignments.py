"""
Assessment Assignment API Routes
Handles assignment of assessments to parents/schools by psychologists
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.core.config import settings
from app.models.user import User, UserRole
from app.models.student import Student
from app.models.assignment import AssessmentAssignment, AssignmentStatus
from app.models.student_guardian import StudentGuardian
from app.utils.email import send_assessment_assignment_email, EmailService
from app.utils.magic_link import create_invite_magic_link

router = APIRouter(prefix="/assignments", tags=["assignments"])


# Pydantic schemas
class AssignmentCreate(BaseModel):
    student_id: UUID
    assigned_to_user_id: UUID
    notes: str | None = None
    due_date: datetime | None = None


class AssignmentResponse(BaseModel):
    id: UUID
    student_id: UUID
    assigned_to_user_id: UUID
    assigned_by_psychologist_id: UUID
    status: str
    notes: str | None
    due_date: datetime | None
    assigned_at: datetime

    class Config:
        from_attributes = True


def require_psychologist_or_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """Dependency to ensure user is psychologist or admin"""
    if current_user.role not in [UserRole.PSYCHOLOGIST, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Psychologist or Admin access required"
        )
    return current_user


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_assignment(
    assignment_data: AssignmentCreate,
    current_user: User = Depends(require_psychologist_or_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new assessment assignment (Psychologist/Admin only)

    Assigns an assessment to a parent or school for a specific student
    """

    # Verify student exists
    result = await db.execute(
        select(Student).where(Student.id == assignment_data.student_id)
    )
    student = result.scalar_one_or_none()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )

    # Verify assigned_to user exists and is PARENT or SCHOOL
    result = await db.execute(
        select(User).where(User.id == assignment_data.assigned_to_user_id)
    )
    assigned_to = result.scalar_one_or_none()

    if not assigned_to:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assigned user not found"
        )

    if assigned_to.role not in [UserRole.PARENT, UserRole.SCHOOL]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only assign to PARENT or SCHOOL users"
        )

    # Verify parent/guardian is linked to the student
    relationship_result = await db.execute(
        select(StudentGuardian).where(
            and_(
                StudentGuardian.student_id == assignment_data.student_id,
                StudentGuardian.guardian_user_id == assignment_data.assigned_to_user_id
            )
        )
    )
    relationship = relationship_result.scalar_one_or_none()

    if not relationship:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"This parent/guardian is not linked to the student. Please add them as a guardian first in the Students tab."
        )

    # Check if there's already an active assignment for this student
    result = await db.execute(
        select(AssessmentAssignment).where(
            and_(
                AssessmentAssignment.student_id == assignment_data.student_id,
                AssessmentAssignment.status.in_([AssignmentStatus.ASSIGNED, AssignmentStatus.IN_PROGRESS])
            )
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student already has an active assessment assignment"
        )

    # Create assignment
    new_assignment = AssessmentAssignment(
        assigned_by_psychologist_id=current_user.id,
        student_id=assignment_data.student_id,
        assigned_to_user_id=assignment_data.assigned_to_user_id,
        notes=assignment_data.notes,
        due_date=assignment_data.due_date,
        status=AssignmentStatus.ASSIGNED
    )

    db.add(new_assignment)
    await db.commit()
    await db.refresh(new_assignment)

    # Send email notification to parent
    try:
        email_service = EmailService(
            smtp_server=settings.SMTP_SERVER,
            smtp_port=settings.SMTP_PORT,
            sender_email=settings.SMTP_USERNAME,
            sender_password=settings.SMTP_PASSWORD,
            use_tls=settings.SMTP_USE_TLS
        )

        # Create magic link token and build assessment link
        magic_link_token = await create_invite_magic_link(
            db=db,
            user_id=assigned_to.id,
            assignment_id=new_assignment.id,
            expiry_hours=settings.MAGIC_LINK_EXPIRY_HOURS,
        )
        assessment_link = f"{settings.FRONTEND_URL}/auth/magic/{magic_link_token.token}"

        # Format due date if present
        due_date_str = None
        if assignment_data.due_date:
            due_date_str = assignment_data.due_date.strftime("%B %d, %Y at %I:%M %p")

        # Send email
        email_sent = send_assessment_assignment_email(
            parent_email=assigned_to.email,
            parent_name=assigned_to.full_name,
            student_name=f"{student.first_name} {student.last_name}",
            psychologist_name=current_user.full_name,
            assessment_link=assessment_link,
            due_date=due_date_str,
            notes=assignment_data.notes,
            email_service=email_service
        )

        if not email_sent:
            # Log warning but don't fail the request
            print(f"Warning: Failed to send email to {assigned_to.email}")

    except Exception as e:
        # Log error but don't fail the request
        print(f"Error sending email: {str(e)}")

    return {
        "message": "Assessment assigned successfully",
        "assignment_id": str(new_assignment.id),
        "student_id": str(new_assignment.student_id),
        "assigned_to": assigned_to.full_name,
        "status": new_assignment.status.value
    }


@router.get("/my-assignments")
async def get_my_assignments(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get assignments for current user (Parent/School)

    Returns all assessment assignments assigned to the logged-in parent or school
    """

    if current_user.role not in [UserRole.PARENT, UserRole.SCHOOL]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents and schools can view assigned assessments"
        )

    result = await db.execute(
        select(AssessmentAssignment).where(
            and_(
                AssessmentAssignment.assigned_to_user_id == current_user.id,
                AssessmentAssignment.status != AssignmentStatus.CANCELLED
            )
        ).order_by(AssessmentAssignment.assigned_at.desc())
    )
    assignments = result.scalars().all()

    # Get student details for each assignment
    assignments_with_details = []
    for assignment in assignments:
        student_result = await db.execute(
            select(Student).where(Student.id == assignment.student_id)
        )
        student = student_result.scalar_one_or_none()

        psychologist_result = await db.execute(
            select(User).where(User.id == assignment.assigned_by_psychologist_id)
        )
        psychologist = psychologist_result.scalar_one_or_none()

        assignments_with_details.append({
            "id": str(assignment.id),
            "student": {
                "id": str(student.id),
                "first_name": student.first_name,
                "last_name": student.last_name,
                "grade_level": student.year_group,
            } if student else None,
            "assigned_by": {
                "name": psychologist.full_name,
                "email": psychologist.email
            } if psychologist else None,
            "status": assignment.status.value,
            "notes": assignment.notes,
            "due_date": assignment.due_date.isoformat() if assignment.due_date else None,
            "assigned_at": assignment.assigned_at.isoformat(),
        })

    return assignments_with_details


@router.get("/psychologist/all")
async def get_all_assignments(
    current_user: User = Depends(require_psychologist_or_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all assignments (Psychologist/Admin only)

    Returns all assessment assignments in the system
    """

    result = await db.execute(
        select(AssessmentAssignment).order_by(AssessmentAssignment.assigned_at.desc())
    )
    assignments = result.scalars().all()

    assignments_with_details = []
    for assignment in assignments:
        student_result = await db.execute(
            select(Student).where(Student.id == assignment.student_id)
        )
        student = student_result.scalar_one_or_none()

        assigned_to_result = await db.execute(
            select(User).where(User.id == assignment.assigned_to_user_id)
        )
        assigned_to = assigned_to_result.scalar_one_or_none()

        assignments_with_details.append({
            "id": str(assignment.id),
            "student": {
                "id": str(student.id),
                "first_name": student.first_name,
                "last_name": student.last_name,
                "grade_level": student.year_group,
            } if student else None,
            "assigned_to": {
                "id": str(assigned_to.id),
                "name": assigned_to.full_name,
                "email": assigned_to.email,
                "role": assigned_to.role.value
            } if assigned_to else None,
            "status": assignment.status.value,
            "notes": assignment.notes,
            "due_date": assignment.due_date.isoformat() if assignment.due_date else None,
            "assigned_at": assignment.assigned_at.isoformat(),
        })

    return assignments_with_details


@router.get("/students-for-assignment")
async def get_students_for_assignment(
    current_user: User = Depends(require_psychologist_or_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all students with their parent/school/guardian info for assignment (Psychologist/Admin only)

    Returns students with their linked guardians
    """

    result = await db.execute(
        select(Student).order_by(Student.school_name, Student.first_name)
    )
    students = result.scalars().all()

    students_with_guardians = []
    for student in students:
        # Get all guardians for this student
        guardians_result = await db.execute(
            select(StudentGuardian).where(StudentGuardian.student_id == student.id)
        )
        guardian_relationships = guardians_result.scalars().all()

        # Fetch guardian user details
        guardians_list = []
        for relationship in guardian_relationships:
            guardian_user_result = await db.execute(
                select(User).where(User.id == relationship.guardian_user_id)
            )
            guardian_user = guardian_user_result.scalar_one_or_none()

            if guardian_user:
                guardians_list.append({
                    "id": str(guardian_user.id),
                    "name": guardian_user.full_name,
                    "email": guardian_user.email,
                    "role": guardian_user.role.value,
                    "relationship_type": relationship.relationship_type,
                    "is_primary": relationship.is_primary
                })

        # Check if student has active assignment
        assignment_result = await db.execute(
            select(AssessmentAssignment).where(
                and_(
                    AssessmentAssignment.student_id == student.id,
                    AssessmentAssignment.status.in_([AssignmentStatus.ASSIGNED, AssignmentStatus.IN_PROGRESS, AssignmentStatus.COMPLETED])
                )
            ).order_by(AssessmentAssignment.assigned_at.desc())
        )
        active_assignment = assignment_result.scalar_one_or_none()

        # Calculate progress from chat session if assignment exists
        progress_pct = 0
        assignment_status = None
        if active_assignment:
            assignment_status = active_assignment.status.value if hasattr(active_assignment.status, 'value') else str(active_assignment.status)
            from app.models.chat import ChatSession
            session_result = await db.execute(
                select(ChatSession).where(
                    ChatSession.assignment_id == active_assignment.id
                ).order_by(ChatSession.started_at.desc())
            )
            chat_session = session_result.scalar_one_or_none()
            if chat_session and chat_session.context_data:
                answered = chat_session.context_data.get("answered_node_ids", [])
                total_nodes = 102  # parent_assessment_v1 answerable nodes
                progress_pct = round((len(answered) / total_nodes) * 100) if total_nodes > 0 else 0
                if chat_session.status == "completed":
                    progress_pct = 100

        students_with_guardians.append({
            "id": str(student.id),
            "first_name": student.first_name,
            "last_name": student.last_name,
            "grade_level": student.year_group,
            "school_name": student.school_name,
            "guardians": guardians_list,
            "has_active_assignment": active_assignment is not None,
            "assignment_status": assignment_status,
            "progress_percentage": progress_pct,
        })

    return students_with_guardians


@router.patch("/{assignment_id}/cancel")
async def cancel_assignment(
    assignment_id: UUID,
    current_user: User = Depends(require_psychologist_or_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Cancel an assessment assignment (Psychologist/Admin only)
    """

    result = await db.execute(
        select(AssessmentAssignment).where(AssessmentAssignment.id == assignment_id)
    )
    assignment = result.scalar_one_or_none()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )

    if assignment.status == AssignmentStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel completed assignment"
        )

    assignment.status = AssignmentStatus.CANCELLED
    await db.commit()

    return {"message": "Assignment cancelled successfully"}
