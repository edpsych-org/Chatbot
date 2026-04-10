"""
Magic Link Utilities
Generate and validate magic link tokens for passwordless authentication
"""

import secrets
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.magic_link import MagicLinkToken
from app.models.user import User


def generate_magic_token() -> str:
    """Generate a secure random token for magic links"""
    return secrets.token_urlsafe(32)


async def create_magic_link(
    db: AsyncSession,
    user_id: str,
    expiry_hours: int = 24
) -> MagicLinkToken:
    """
    Create a new magic link token for a user

    Args:
        db: Database session
        user_id: UUID of the user
        expiry_hours: How many hours until the link expires (default 24)

    Returns:
        MagicLinkToken object
    """
    token = generate_magic_token()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=expiry_hours)

    magic_link = MagicLinkToken(
        user_id=user_id,
        token=token,
        expires_at=expires_at
    )

    db.add(magic_link)
    await db.commit()
    await db.refresh(magic_link)

    return magic_link


async def verify_magic_link(
    db: AsyncSession,
    token: str,
    consume: bool = True
) -> tuple[User | None, MagicLinkToken | None]:
    """
    Verify a magic link token and return the associated user and token record.
    When consume=False, the token is NOT marked as used (for password setup flow).
    """
    result = await db.execute(
        select(MagicLinkToken).where(MagicLinkToken.token == token)
    )
    magic_link = result.scalar_one_or_none()

    if not magic_link:
        return None, None

    if not magic_link.is_valid():
        return None, None

    if consume:
        magic_link.used_at = datetime.now(timezone.utc)
        await db.commit()

    result = await db.execute(
        select(User).where(User.id == magic_link.user_id)
    )
    user = result.scalar_one_or_none()

    return user, magic_link


async def create_invite_magic_link(
    db: AsyncSession,
    user_id: str,
    assignment_id: str,
    expiry_hours: int = 48
) -> MagicLinkToken:
    """Create a magic link tied to a specific assessment assignment."""
    token = generate_magic_token()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=expiry_hours)

    magic_link = MagicLinkToken(
        user_id=user_id,
        token=token,
        expires_at=expires_at,
        assignment_id=assignment_id,
        purpose="assessment_invite"
    )

    db.add(magic_link)
    await db.commit()
    await db.refresh(magic_link)

    return magic_link


async def cleanup_expired_tokens(db: AsyncSession) -> int:
    """
    Delete expired or used magic link tokens

    Args:
        db: Database session

    Returns:
        Number of tokens deleted
    """
    from sqlalchemy import delete

    # Delete tokens that are expired or already used
    result = await db.execute(
        delete(MagicLinkToken).where(
            (MagicLinkToken.expires_at < datetime.now(timezone.utc)) |
            (MagicLinkToken.used_at.isnot(None))
        )
    )
    await db.commit()

    return result.rowcount
