"""
Create Test Users for EdPsych AI
Run this script to create test users for all roles
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
import bcrypt

from app.core.config import settings
from app.models.user import User, UserRole

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=False
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


async def create_test_users():
    """Create test users for all roles"""

    test_users = [
        {
            "email": "psychologist@test.com",
            "password": "test123",
            "role": UserRole.PSYCHOLOGIST,
            "full_name": "Dr. Sarah Johnson",
            "phone": "+1-555-0101",
            "is_verified": True,
            "is_active": True
        },
        {
            "email": "admin@test.com",
            "password": "admin123",
            "role": UserRole.ADMIN,
            "full_name": "Admin User",
            "phone": "+1-555-0100",
            "is_verified": True,
            "is_active": True
        },
        {
            "email": "parent@test.com",
            "password": "parent123",
            "role": UserRole.PARENT,
            "full_name": "Jane Smith",
            "phone": "+1-555-0102",
            "is_verified": True,
            "is_active": True
        },
        {
            "email": "school@test.com",
            "password": "school123",
            "role": UserRole.SCHOOL,
            "full_name": "Springfield High School",
            "phone": "+1-555-0103",
            "is_verified": True,
            "is_active": True
        }
    ]

    async with AsyncSessionLocal() as session:
        print("\n" + "="*60)
        print("Creating Test Users for EdPsych AI")
        print("="*60 + "\n")

        created_count = 0
        updated_count = 0

        for user_data in test_users:
            # Check if user already exists
            result = await session.execute(
                select(User).where(User.email == user_data["email"])
            )
            existing_user = result.scalar_one_or_none()

            if existing_user:
                # Update existing user
                existing_user.password_hash = hash_password(user_data["password"])
                existing_user.full_name = user_data["full_name"]
                existing_user.phone = user_data["phone"]
                existing_user.is_verified = user_data["is_verified"]
                existing_user.is_active = user_data["is_active"]
                updated_count += 1
                print(f"[UPDATED] {user_data['role'].value:12} | {user_data['email']:25} | Password: {user_data['password']}")
            else:
                # Create new user
                new_user = User(
                    email=user_data["email"],
                    password_hash=hash_password(user_data["password"]),
                    role=user_data["role"],
                    full_name=user_data["full_name"],
                    phone=user_data["phone"],
                    is_verified=user_data["is_verified"],
                    is_active=user_data["is_active"]
                )
                session.add(new_user)
                created_count += 1
                print(f"[CREATED] {user_data['role'].value:12} | {user_data['email']:25} | Password: {user_data['password']}")

        await session.commit()

        print("\n" + "="*60)
        print(f"Summary: {created_count} created, {updated_count} updated")
        print("="*60 + "\n")

        print("Test users ready! Use these credentials to login:")
        print("\nPSYCHOLOGIST LOGIN:")
        print("  Email:    psychologist@test.com")
        print("  Password: test123")

        print("\nADMIN LOGIN:")
        print("  Email:    admin@test.com")
        print("  Password: admin123")

        print("\nPARENT LOGIN:")
        print("  Email:    parent@test.com")
        print("  Password: parent123")

        print("\nSCHOOL LOGIN:")
        print("  Email:    school@test.com")
        print("  Password: school123")
        print()


if __name__ == "__main__":
    asyncio.run(create_test_users())
