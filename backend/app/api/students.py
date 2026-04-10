"""
Students API Routes
CRUD operations for students
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.student import Student
from app.schemas.student import StudentCreate, StudentUpdate, StudentResponse

router = APIRouter()


@router.post("/", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def create_student(
    student_data: StudentCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new student profile

    - **first_name**: Student's first name
    - **last_name**: Student's last name
    - **date_of_birth**: Student's date of birth (YYYY-MM-DD)
    - **gender**: Optional gender
    - **school_name**: Optional school name
    - **year_group**: Optional year/grade

    Requires authentication
    """
    new_student = Student(
        first_name=student_data.first_name,
        last_name=student_data.last_name,
        date_of_birth=student_data.date_of_birth,
        gender=student_data.gender,
        school_name=student_data.school_name,
        year_group=student_data.year_group,
        created_by_user_id=current_user.id
    )

    db.add(new_student)
    await db.commit()
    await db.refresh(new_student)

    return new_student


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(
    student_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get student by ID

    Returns student details if user has access
    """
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )

    # Check access: user must be creator, psychologist, or admin
    if (student.created_by_user_id != current_user.id and
        current_user.role.value not in ["PSYCHOLOGIST", "ADMIN"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this student"
        )

    return student


@router.get("/", response_model=List[StudentResponse])
async def list_students(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List students

    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return

    Returns students created by current user (parents/schools)
    or all students (psychologists/admin)
    """
    query = select(Student)

    # Filter by creator for parents/schools
    if current_user.role.value not in ["PSYCHOLOGIST", "ADMIN"]:
        query = query.where(Student.created_by_user_id == current_user.id)

    # Add pagination
    query = query.offset(skip).limit(limit).order_by(Student.created_at.desc())

    result = await db.execute(query)
    students = result.scalars().all()

    return students


@router.patch("/{student_id}", response_model=StudentResponse)
async def update_student(
    student_id: UUID,
    student_data: StudentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update student information

    Only the creator, psychologists, or admins can update
    """
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )

    # Check access
    if (student.created_by_user_id != current_user.id and
        current_user.role.value not in ["PSYCHOLOGIST", "ADMIN"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this student"
        )

    # Update fields
    update_data = student_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(student, field, value)

    await db.commit()
    await db.refresh(student)

    return student


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student(
    student_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a student

    Only admins can delete students
    """
    if current_user.role.value != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete students"
        )

    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )

    await db.delete(student)
    await db.commit()

    return None


@router.get("/all/with-parents")
async def list_all_students_with_parents(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all students with parent information (for school/admin dashboards)

    Returns students with embedded parent details
    """
    # Only schools, psychologists, and admins can access
    if current_user.role.value not in ["SCHOOL", "PSYCHOLOGIST", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access all students"
        )

    result = await db.execute(
        select(Student).order_by(Student.created_at.desc())
    )
    students = result.scalars().all()

    # Get parent information for each student
    students_with_parents = []
    for student in students:
        parent_result = await db.execute(
            select(User).where(User.id == student.created_by_user_id)
        )
        parent = parent_result.scalar_one_or_none()

        students_with_parents.append({
            "id": student.id,
            "first_name": student.first_name,
            "last_name": student.last_name,
            "date_of_birth": student.date_of_birth.isoformat() if student.date_of_birth else None,
            "grade_level": student.year_group,
            "school_name": student.school_name,
            "created_at": student.created_at.isoformat() if student.created_at else None,
            "parent": {
                "full_name": parent.full_name if parent else None,
                "email": parent.email if parent else None,
            }
        })

    return students_with_parents
