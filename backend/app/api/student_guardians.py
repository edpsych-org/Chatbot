"""
Student-Guardian Relationship API Routes
Manages parent/guardian relationships with students
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List
from uuid import UUID
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User, UserRole
from app.models.student import Student
from app.models.student_guardian import StudentGuardian
from app.utils.magic_link import create_magic_link
from app.utils.email import send_parent_invitation_email, EmailService
from app.core.config import settings

router = APIRouter(prefix="/student-guardians", tags=["student-guardians"])


# Pydantic schemas
class StudentGuardianCreate(BaseModel):
    student_id: UUID
    guardian_user_id: UUID
    relationship_type: str | None = None
    is_primary: str = "false"


class StudentGuardianResponse(BaseModel):
    id: UUID
    student_id: UUID
    guardian_user_id: UUID
    relationship_type: str | None
    is_primary: str
    student: dict
    guardian: dict

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
async def create_student_guardian_relationship(
    relationship_data: StudentGuardianCreate,
    current_user: User = Depends(require_psychologist_or_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a student-guardian relationship (Psychologist/Admin only)

    Links a parent/guardian to a student. This relationship is used to:
    - Validate assignment permissions
    - Allow parents to see only their students
    - Support multiple guardians per student
    """

    # Verify student exists
    result = await db.execute(
        select(Student).where(Student.id == relationship_data.student_id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )

    # Verify guardian exists and is PARENT or SCHOOL
    result = await db.execute(
        select(User).where(User.id == relationship_data.guardian_user_id)
    )
    guardian = result.scalar_one_or_none()
    if not guardian:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Guardian user not found"
        )

    if guardian.role not in [UserRole.PARENT, UserRole.SCHOOL]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Guardian must be a PARENT or SCHOOL user"
        )

    # Check if relationship already exists
    result = await db.execute(
        select(StudentGuardian).where(
            and_(
                StudentGuardian.student_id == relationship_data.student_id,
                StudentGuardian.guardian_user_id == relationship_data.guardian_user_id
            )
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This guardian is already linked to this student"
        )

    # Create the relationship
    new_relationship = StudentGuardian(
        student_id=relationship_data.student_id,
        guardian_user_id=relationship_data.guardian_user_id,
        relationship_type=relationship_data.relationship_type,
        is_primary=relationship_data.is_primary,
        created_by_user_id=current_user.id
    )

    db.add(new_relationship)
    await db.commit()
    await db.refresh(new_relationship)

    return {
        "id": new_relationship.id,
        "student_id": new_relationship.student_id,
        "guardian_user_id": new_relationship.guardian_user_id,
        "relationship_type": new_relationship.relationship_type,
        "is_primary": new_relationship.is_primary,
        "message": "Student-guardian relationship created successfully"
    }


@router.get("/student/{student_id}/guardians")
async def get_student_guardians(
    student_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all guardians for a specific student"""

    # Verify student exists
    result = await db.execute(
        select(Student).where(Student.id == student_id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )

    # Get all guardian relationships
    result = await db.execute(
        select(StudentGuardian).where(StudentGuardian.student_id == student_id)
    )
    relationships = result.scalars().all()

    # Fetch guardian details
    guardians = []
    for rel in relationships:
        guardian_result = await db.execute(
            select(User).where(User.id == rel.guardian_user_id)
        )
        guardian = guardian_result.scalar_one_or_none()

        if guardian:
            guardians.append({
                "relationship_id": rel.id,
                "guardian_id": guardian.id,
                "guardian_name": guardian.full_name,
                "guardian_email": guardian.email,
                "guardian_role": guardian.role.value,
                "relationship_type": rel.relationship_type,
                "is_primary": rel.is_primary
            })

    return guardians


@router.get("/guardian/{guardian_user_id}/students")
async def get_guardian_students(
    guardian_user_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all students for a specific guardian"""

    # Only allow users to see their own students unless they're psychologist/admin
    if current_user.role not in [UserRole.PSYCHOLOGIST, UserRole.ADMIN]:
        if current_user.id != guardian_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own students"
            )

    # Get all student relationships
    result = await db.execute(
        select(StudentGuardian).where(StudentGuardian.guardian_user_id == guardian_user_id)
    )
    relationships = result.scalars().all()

    # Fetch student details
    students = []
    for rel in relationships:
        student_result = await db.execute(
            select(Student).where(Student.id == rel.student_id)
        )
        student = student_result.scalar_one_or_none()

        if student:
            students.append({
                "relationship_id": rel.id,
                "student_id": student.id,
                "student_name": f"{student.first_name} {student.last_name}",
                "first_name": student.first_name,
                "last_name": student.last_name,
                "grade_level": student.year_group,
                "school_name": student.school_name,
                "relationship_type": rel.relationship_type,
                "is_primary": rel.is_primary
            })

    return students


class InviteParentRequest(BaseModel):
    student_id: UUID
    parent_email: str
    parent_name: str
    relationship_type: str | None = "Guardian"
    is_primary: str = "true"


@router.post("/invite-parent", status_code=status.HTTP_201_CREATED)
async def invite_parent_and_link(
    invite_data: InviteParentRequest,
    current_user: User = Depends(require_psychologist_or_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a parent account and automatically link them to the student (Psychologist/Admin only)

    This endpoint solves the problem when a psychologist needs to assign an assessment
    but the parent doesn't exist in the system yet.

    Steps:
    1. Check if parent email already exists
    2. If not, create parent account with temporary password
    3. Link parent to student
    4. Return parent credentials
    """

    # Verify student exists
    result = await db.execute(
        select(Student).where(Student.id == invite_data.student_id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )

    # Check if parent email already exists
    result = await db.execute(
        select(User).where(User.email == invite_data.parent_email)
    )
    existing_parent = result.scalar_one_or_none()

    if existing_parent:
        # Parent already exists, just link them to student
        if existing_parent.role not in [UserRole.PARENT, UserRole.SCHOOL]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email belongs to a user who is not a parent or school"
            )

        # Check if relationship already exists
        result = await db.execute(
            select(StudentGuardian).where(
                and_(
                    StudentGuardian.student_id == invite_data.student_id,
                    StudentGuardian.guardian_user_id == existing_parent.id
                )
            )
        )
        existing_relationship = result.scalar_one_or_none()

        if existing_relationship:
            return {
                "message": "Parent already linked to student",
                "parent": {
                    "id": str(existing_parent.id),
                    "name": existing_parent.full_name,
                    "email": existing_parent.email,
                    "already_existed": True
                }
            }

        # Create relationship
        new_relationship = StudentGuardian(
            student_id=invite_data.student_id,
            guardian_user_id=existing_parent.id,
            relationship_type=invite_data.relationship_type,
            is_primary=invite_data.is_primary,
            created_by_user_id=current_user.id
        )

        db.add(new_relationship)
        await db.commit()

        return {
            "message": "Existing parent linked to student successfully",
            "parent": {
                "id": str(existing_parent.id),
                "name": existing_parent.full_name,
                "email": existing_parent.email,
                "already_existed": True
            }
        }

    # Create new parent account
    from app.core.security import get_password_hash
    import secrets

    # Generate a secure random password (won't be shared, only for account security)
    # Parent will use magic link to login
    temp_password = f"Parent{secrets.randbelow(10000):04d}!{secrets.token_urlsafe(8)}"
    hashed_password = get_password_hash(temp_password)

    new_parent = User(
        email=invite_data.parent_email,
        password_hash=hashed_password,
        full_name=invite_data.parent_name,
        role=UserRole.PARENT
    )

    db.add(new_parent)
    await db.flush()  # Get the ID before committing

    # Create student-guardian relationship
    new_relationship = StudentGuardian(
        student_id=invite_data.student_id,
        guardian_user_id=new_parent.id,
        relationship_type=invite_data.relationship_type,
        is_primary=invite_data.is_primary,
        created_by_user_id=current_user.id
    )

    db.add(new_relationship)
    await db.commit()
    await db.refresh(new_parent)

    # Generate magic link for passwordless login
    magic_link_token = await create_magic_link(db, str(new_parent.id), expiry_hours=24)
    magic_link_url = f"{settings.FRONTEND_URL}/auth/magic-login?token={magic_link_token.token}"

    # Send invitation email with magic link
    try:
        email_service = EmailService(
            smtp_server=settings.SMTP_SERVER,
            smtp_port=settings.SMTP_PORT,
            sender_email=settings.SMTP_USERNAME,
            sender_password=settings.SMTP_PASSWORD,
            use_tls=settings.SMTP_USE_TLS
        )

        email_sent = send_parent_invitation_email(
            parent_email=new_parent.email,
            parent_name=new_parent.full_name,
            student_name=f"{student.first_name} {student.last_name}",
            psychologist_name=current_user.full_name,
            magic_link=magic_link_url,
            email_service=email_service
        )

        email_status = "sent" if email_sent else "failed"
    except Exception as e:
        print(f"Error sending invitation email: {str(e)}")
        email_status = "error"

    return {
        "message": "Parent account created and invitation email sent",
        "parent": {
            "id": str(new_parent.id),
            "name": new_parent.full_name,
            "email": new_parent.email,
            "already_existed": False
        },
        "email_status": email_status,
        "magic_link": magic_link_url,  # For testing/development - can be removed in production
        "note": "Parent will receive an email with a one-click login link. No password needed!"
    }


@router.delete("/{relationship_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student_guardian_relationship(
    relationship_id: UUID,
    current_user: User = Depends(require_psychologist_or_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete a student-guardian relationship (Psychologist/Admin only)"""

    result = await db.execute(
        select(StudentGuardian).where(StudentGuardian.id == relationship_id)
    )
    relationship = result.scalar_one_or_none()

    if not relationship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Relationship not found"
        )

    await db.delete(relationship)
    await db.commit()

    return None


@router.get("/parent-users")
async def get_parent_users(
    current_user: User = Depends(require_psychologist_or_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get all parent/school users (for dropdown in UI)"""

    result = await db.execute(
        select(User).where(
            User.role.in_([UserRole.PARENT, UserRole.SCHOOL])
        ).order_by(User.full_name)
    )
    users = result.scalars().all()

    return [
        {
            "id": str(user.id),
            "name": user.full_name,
            "email": user.email,
            "role": user.role.value
        }
        for user in users
    ]
