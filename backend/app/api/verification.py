"""
Parent Verification API Routes
Multi-layer verification system for secure assessment access
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional

from app.core.database import get_db
from app.models.verification_token import VerificationToken
from app.models.student import Student
from app.models.user import User

router = APIRouter(prefix="/verification", tags=["verification"])


# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================

class OTPVerifyRequest(BaseModel):
    """OTP verification request"""
    secure_token: str
    otp_code: str


class DOBVerifyRequest(BaseModel):
    """Date of Birth verification request"""
    secure_token: str
    date_of_birth: str  # YYYY-MM-DD format


class VerificationStatusResponse(BaseModel):
    """Verification status response"""
    is_otp_verified: bool
    is_dob_verified: bool
    is_fully_verified: bool
    student_name: Optional[str] = None
    assessment_link: Optional[str] = None


# ============================================================================
# TOKEN VALIDATION
# ============================================================================

@router.get("/status/{secure_token}")
async def get_verification_status(
    secure_token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Check verification status of a secure token

    Returns:
    - Token exists and is valid
    - Which verification steps are complete
    - Student information (if token is valid)
    """

    # Find token
    result = await db.execute(
        select(VerificationToken).where(VerificationToken.secure_token == secure_token)
    )
    token = result.scalar_one_or_none()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired verification link"
        )

    # Check if token is expired
    if token.is_expired():
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This verification link has expired. Please contact your psychologist for a new link."
        )

    # Get student information
    student_result = await db.execute(
        select(Student).where(Student.id == token.student_id)
    )
    student = student_result.scalar_one_or_none()

    return {
        "valid": True,
        "is_otp_verified": token.is_otp_verified,
        "is_dob_verified": token.is_dob_verified,
        "is_fully_verified": token.is_fully_verified,
        "student_name": f"{student.first_name} {student.last_name}" if student else None,
        "expires_at": token.expires_at.isoformat(),
        "otp_attempts_remaining": 5 - int(token.otp_attempts),
        "dob_attempts_remaining": 3 - int(token.dob_attempts)
    }


# ============================================================================
# STEP 1: OTP VERIFICATION
# ============================================================================

@router.post("/verify-otp", status_code=status.HTTP_200_OK)
async def verify_otp(
    request: OTPVerifyRequest,
    req: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify OTP code (Step 1 of 2)

    Workflow:
    1. Parent receives secure link + OTP
    2. Parent clicks link -> enters OTP
    3. System validates OTP
    4. If valid -> proceed to DOB verification
    5. If invalid -> increment attempts counter
    """

    # Find token
    result = await db.execute(
        select(VerificationToken).where(
            VerificationToken.secure_token == request.secure_token
        )
    )
    token = result.scalar_one_or_none()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid verification link"
        )

    # Check if token is expired
    if token.is_expired():
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This verification link has expired"
        )

    # Check if already verified
    if token.is_otp_verified:
        return {
            "success": True,
            "message": "OTP already verified. Please proceed to date of birth verification.",
            "next_step": "dob_verification"
        }

    # Check attempt limit
    if not token.can_attempt_otp():
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed OTP attempts. Please contact your psychologist for a new link."
        )

    # Verify OTP
    if request.otp_code != token.otp_code:
        token.increment_otp_attempts()

        # Store IP and user agent for security
        token.ip_address = req.client.host if req.client else None
        token.user_agent = req.headers.get("user-agent")

        await db.commit()

        attempts_remaining = 5 - int(token.otp_attempts)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid OTP code. {attempts_remaining} attempts remaining."
        )

    # OTP is correct - mark as verified
    token.mark_otp_verified()
    token.ip_address = req.client.host if req.client else None
    token.user_agent = req.headers.get("user-agent")

    await db.commit()

    return {
        "success": True,
        "message": "OTP verified successfully",
        "next_step": "dob_verification",
        "is_otp_verified": True,
        "is_dob_verified": False,
        "is_fully_verified": False
    }


# ============================================================================
# STEP 2: DATE OF BIRTH VERIFICATION
# ============================================================================

@router.post("/verify-dob", status_code=status.HTTP_200_OK)
async def verify_date_of_birth(
    request: DOBVerifyRequest,
    req: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify student's date of birth (Step 2 of 2)

    Workflow:
    1. Parent has verified OTP
    2. Parent enters student's date of birth
    3. System validates DOB against student record
    4. If valid -> grant full access to assessment
    5. If invalid -> increment attempts counter
    """

    # Find token
    result = await db.execute(
        select(VerificationToken).where(
            VerificationToken.secure_token == request.secure_token
        )
    )
    token = result.scalar_one_or_none()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid verification link"
        )

    # Check if token is expired
    if token.is_expired():
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This verification link has expired"
        )

    # Check if OTP was verified first
    if not token.is_otp_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify OTP first before entering date of birth"
        )

    # Check if already fully verified
    if token.is_fully_verified:
        # Get assessment link
        assessment_link = f"/assessment/{token.assignment_id}"

        return {
            "success": True,
            "message": "Verification already complete. Access granted.",
            "is_fully_verified": True,
            "assessment_link": assessment_link,
            "assignment_id": str(token.assignment_id)
        }

    # Check attempt limit
    if not token.can_attempt_dob():
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed attempts. Please contact your psychologist."
        )

    # Get student's actual date of birth
    student_result = await db.execute(
        select(Student).where(Student.id == token.student_id)
    )
    student = student_result.scalar_one_or_none()

    if not student or not student.date_of_birth:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Student information not found"
        )

    # Parse provided date of birth
    try:
        provided_dob = datetime.strptime(request.date_of_birth, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Please use YYYY-MM-DD format."
        )

    # Verify DOB matches
    if provided_dob != student.date_of_birth:
        token.increment_dob_attempts()

        # Store IP and user agent for security
        token.ip_address = req.client.host if req.client else None
        token.user_agent = req.headers.get("user-agent")

        await db.commit()

        attempts_remaining = 3 - int(token.dob_attempts)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Incorrect date of birth. {attempts_remaining} attempts remaining."
        )

    # DOB is correct - mark as fully verified
    token.mark_dob_verified()
    token.ip_address = req.client.host if req.client else None
    token.user_agent = req.headers.get("user-agent")

    await db.commit()

    # Generate assessment access link
    assessment_link = f"/assessment/{token.assignment_id}"

    return {
        "success": True,
        "message": "Verification complete! You now have access to the assessment.",
        "is_otp_verified": True,
        "is_dob_verified": True,
        "is_fully_verified": True,
        "assessment_link": assessment_link,
        "assignment_id": str(token.assignment_id),
        "student_name": f"{student.first_name} {student.last_name}"
    }


# ============================================================================
# RESEND OTP (Optional - for future use)
# ============================================================================

@router.post("/resend-otp/{secure_token}")
async def resend_otp(
    secure_token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Resend OTP code to parent (email/SMS)
    Future implementation - requires notification service
    """

    result = await db.execute(
        select(VerificationToken).where(
            VerificationToken.secure_token == secure_token
        )
    )
    token = result.scalar_one_or_none()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid verification link"
        )

    if token.is_expired():
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This verification link has expired"
        )

    # TODO: Implement email/SMS notification service
    # await send_otp_notification(token.parent_user_id, token.otp_code)

    return {
        "success": True,
        "message": "OTP resent successfully (feature coming soon)"
    }
