"""
Chatbot API Routes
Assessment sessions, questions, answers
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List
from uuid import UUID
import secrets

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User, UserRole
from app.models.student import Student
from app.models.assignment import AssessmentAssignment, AssignmentStatus
from app.models.assessment import (
    AssessmentSession,
    ChatbotQuestion,
    ChatbotAnswer,
    SessionStatus
)
from app.schemas.assessment import (
    SessionCreate,
    SessionResponse,
    QuestionResponse,
    AnswerSubmit,
    AnswerResponse,
    SessionProgressResponse
)

router = APIRouter()


@router.post("/sessions/start", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def start_session(
    session_data: SessionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Start a new chatbot assessment session for a student.

    - **student_id**: UUID of the student to assess
    - Returns session with unique resume token
    """
    # Verify student exists
    result = await db.execute(
        select(Student).where(Student.id == session_data.student_id)
    )
    student = result.scalar_one_or_none()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )

    # For PARENT/SCHOOL users, verify they have an active assignment for this student
    if current_user.role in [UserRole.PARENT, UserRole.SCHOOL]:
        result = await db.execute(
            select(AssessmentAssignment).where(
                and_(
                    AssessmentAssignment.student_id == session_data.student_id,
                    AssessmentAssignment.assigned_to_user_id == current_user.id,
                    AssessmentAssignment.status.in_([AssignmentStatus.ASSIGNED, AssignmentStatus.IN_PROGRESS])
                )
            )
        )
        assignment = result.scalar_one_or_none()

        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No active assignment found for this student. Please contact your psychologist."
            )

        # Update assignment status to IN_PROGRESS if it's still ASSIGNED
        if assignment.status == AssignmentStatus.ASSIGNED:
            assignment.status = AssignmentStatus.IN_PROGRESS
            await db.commit()

    # For PSYCHOLOGIST/ADMIN, verify they created the student
    elif current_user.role in [UserRole.PSYCHOLOGIST, UserRole.ADMIN]:
        if student.created_by_user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied - you did not create this student"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Check if there's already an active session for this student
    result = await db.execute(
        select(AssessmentSession).where(
            and_(
                AssessmentSession.student_id == session_data.student_id,
                AssessmentSession.status.in_(['DRAFT', 'IN_PROGRESS'])
            )
        ).order_by(AssessmentSession.created_at.desc())
    )
    existing_session = result.scalars().first()

    if existing_session:
        # Return existing session instead of creating new one
        return existing_session

    # Generate unique resume token
    resume_token = secrets.token_urlsafe(32)

    # Create new session (use string value for VARCHAR column)
    new_session = AssessmentSession(
        student_id=session_data.student_id,
        parent_id=current_user.id,
        status='IN_PROGRESS',
        resume_token=resume_token,
        progress_percentage=0
    )

    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)

    return new_session


@router.get("/questions", response_model=List[QuestionResponse])
async def get_questions(
    section: str = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all chatbot questions, optionally filtered by section.

    - **section**: Optional section name to filter questions
    """
    query = select(ChatbotQuestion).order_by(ChatbotQuestion.order_index)

    if section:
        query = query.where(ChatbotQuestion.section == section)

    result = await db.execute(query)
    questions = result.scalars().all()

    return questions


@router.post("/answer", response_model=AnswerResponse, status_code=status.HTTP_201_CREATED)
async def submit_answer(
    answer_data: AnswerSubmit,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit or update an answer to a question.

    - **session_token**: Resume token of the assessment session
    - **question_id**: UUID of the question being answered
    - **answer_text**: Text answer (for TEXT questions)
    - **answer_data**: Structured data answer (for MCQ, SCALE, etc.)
    """
    # Verify session exists and belongs to user by token
    result = await db.execute(
        select(AssessmentSession).where(
            and_(
                AssessmentSession.resume_token == answer_data.session_token,
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

    if session.status not in ['DRAFT', 'IN_PROGRESS']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot submit answer to completed or submitted session"
        )

    # Verify question exists
    result = await db.execute(
        select(ChatbotQuestion).where(ChatbotQuestion.id == answer_data.question_id)
    )
    question = result.scalar_one_or_none()

    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )

    # Check if answer already exists
    result = await db.execute(
        select(ChatbotAnswer).where(
            and_(
                ChatbotAnswer.session_id == session.id,
                ChatbotAnswer.question_id == answer_data.question_id
            )
        )
    )
    existing_answer = result.scalar_one_or_none()

    if existing_answer:
        # Update existing answer
        existing_answer.answer_text = answer_data.answer_text
        existing_answer.answer_data = answer_data.answer_data
        existing_answer.is_complete = True
        await db.commit()
        await db.refresh(existing_answer)
        answer = existing_answer
    else:
        # Create new answer
        new_answer = ChatbotAnswer(
            session_id=session.id,
            question_id=answer_data.question_id,
            answer_text=answer_data.answer_text,
            answer_data=answer_data.answer_data,
            is_complete=True
        )
        db.add(new_answer)
        await db.commit()
        await db.refresh(new_answer)
        answer = new_answer

    # Update session progress
    await update_session_progress(session.id, db)

    return answer


@router.get("/sessions/{session_id}/progress", response_model=SessionProgressResponse)
async def get_session_progress(
    session_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed progress information for a session.

    - **session_id**: UUID of the assessment session
    - Returns session details, progress percentage, and next unanswered question
    """
    # Get session
    result = await db.execute(
        select(AssessmentSession).where(
            and_(
                AssessmentSession.id == session_id,
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

    # Get total question count
    result = await db.execute(select(func.count(ChatbotQuestion.id)))
    total_questions = result.scalar()

    # Get answered questions count
    result = await db.execute(
        select(func.count(ChatbotAnswer.id)).where(
            and_(
                ChatbotAnswer.session_id == session_id,
                ChatbotAnswer.is_complete == True
            )
        )
    )
    answered_questions = result.scalar()

    # Calculate progress
    progress_percentage = int((answered_questions / total_questions * 100)) if total_questions > 0 else 0

    # Get next unanswered question
    result = await db.execute(
        select(ChatbotQuestion)
        .where(
            ChatbotQuestion.id.notin_(
                select(ChatbotAnswer.question_id).where(
                    and_(
                        ChatbotAnswer.session_id == session_id,
                        ChatbotAnswer.is_complete == True
                    )
                )
            )
        )
        .order_by(ChatbotQuestion.order_index)
        .limit(1)
    )
    next_question = result.scalar_one_or_none()

    return SessionProgressResponse(
        session=session,
        total_questions=total_questions,
        answered_questions=answered_questions,
        progress_percentage=progress_percentage,
        next_question=next_question
    )


@router.get("/progress/{token}", response_model=SessionProgressResponse)
async def get_progress_by_token(
    token: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed progress information for a session using resume token.

    - **token**: Resume token of the assessment session
    - Returns session details, progress percentage, and next unanswered question
    """
    # Get session by resume token
    result = await db.execute(
        select(AssessmentSession).where(
            and_(
                AssessmentSession.resume_token == token,
                AssessmentSession.parent_id == current_user.id
            )
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or invalid token"
        )

    # Get total question count
    result = await db.execute(select(func.count(ChatbotQuestion.id)))
    total_questions = result.scalar()

    # Get answered questions count
    result = await db.execute(
        select(func.count(ChatbotAnswer.id)).where(
            and_(
                ChatbotAnswer.session_id == session.id,
                ChatbotAnswer.is_complete == True
            )
        )
    )
    answered_questions = result.scalar()

    # Calculate progress
    progress_percentage = int((answered_questions / total_questions * 100)) if total_questions > 0 else 0

    # Get next unanswered question
    result = await db.execute(
        select(ChatbotQuestion)
        .where(
            ChatbotQuestion.id.notin_(
                select(ChatbotAnswer.question_id).where(
                    and_(
                        ChatbotAnswer.session_id == session.id,
                        ChatbotAnswer.is_complete == True
                    )
                )
            )
        )
        .order_by(ChatbotQuestion.order_index)
        .limit(1)
    )
    next_question = result.scalar_one_or_none()

    return SessionProgressResponse(
        session=session,
        total_questions=total_questions,
        answered_questions=answered_questions,
        progress_percentage=progress_percentage,
        next_question=next_question
    )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get session details by ID.

    - **session_id**: UUID of the assessment session
    """
    result = await db.execute(
        select(AssessmentSession).where(
            and_(
                AssessmentSession.id == session_id,
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

    return session


@router.get("/resume/{token}", response_model=SessionResponse)
async def resume_session(
    token: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Resume a session using its unique resume token.

    - **token**: Unique resume token provided when session was created
    """
    result = await db.execute(
        select(AssessmentSession).where(
            and_(
                AssessmentSession.resume_token == token,
                AssessmentSession.parent_id == current_user.id
            )
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or invalid token"
        )

    return session


@router.post("/sessions/{session_id}/complete", response_model=SessionResponse)
async def complete_session(
    session_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark a session as completed.

    - **session_id**: UUID of the assessment session
    """
    result = await db.execute(
        select(AssessmentSession).where(
            and_(
                AssessmentSession.id == session_id,
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

    if session.status == 'SUBMITTED':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session already submitted"
        )

    session.status = 'COMPLETED'
    await db.commit()
    await db.refresh(session)

    return session


async def update_session_progress(session_id: UUID, db: AsyncSession):
    """Helper function to update session progress percentage"""
    # Get total question count
    result = await db.execute(select(func.count(ChatbotQuestion.id)))
    total_questions = result.scalar()

    # Get answered questions count
    result = await db.execute(
        select(func.count(ChatbotAnswer.id)).where(
            and_(
                ChatbotAnswer.session_id == session_id,
                ChatbotAnswer.is_complete == True
            )
        )
    )
    answered_questions = result.scalar()

    # Calculate progress
    progress_percentage = int((answered_questions / total_questions * 100)) if total_questions > 0 else 0

    # Update session
    result = await db.execute(
        select(AssessmentSession).where(AssessmentSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if session:
        session.progress_percentage = progress_percentage

        # Mark as completed if all questions are answered
        if answered_questions == total_questions and total_questions > 0:
            session.status = 'COMPLETED'
            session.completed_at = func.now()

        await db.commit()
