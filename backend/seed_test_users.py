"""
Seed Test User Accounts
Creates test accounts for Parents, Psychologists, and Admin users
"""

import asyncio
from sqlalchemy import select
from app.core.database import engine, AsyncSessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash


async def seed_test_users():
    """Create test user accounts"""
    print("=" * 60)
    print("SEEDING TEST USER ACCOUNTS")
    print("=" * 60)

    test_users = [
        # Parent Accounts
        {
            "email": "parent1@test.com",
            "password": "Parent@123",
            "role": UserRole.PARENT,
            "full_name": "Sarah Johnson",
            "phone": "+1-555-0101",
            "organization": None
        },
        {
            "email": "parent2@test.com",
            "password": "Parent@123",
            "role": UserRole.PARENT,
            "full_name": "Michael Chen",
            "phone": "+1-555-0102",
            "organization": None
        },
        {
            "email": "parent3@test.com",
            "password": "Parent@123",
            "role": UserRole.PARENT,
            "full_name": "Emily Rodriguez",
            "phone": "+1-555-0103",
            "organization": None
        },
        {
            "email": "parent4@test.com",
            "password": "Parent@123",
            "role": UserRole.PARENT,
            "full_name": "David Thompson",
            "phone": "+1-555-0104",
            "organization": None
        },

        # Psychologist Accounts (Dr.)
        {
            "email": "dr.smith@test.com",
            "password": "Doctor@123",
            "role": UserRole.PSYCHOLOGIST,
            "full_name": "Dr. Jennifer Smith",
            "phone": "+1-555-0201",
            "organization": "Mindful Psychology Clinic"
        },
        {
            "email": "dr.patel@test.com",
            "password": "Doctor@123",
            "role": UserRole.PSYCHOLOGIST,
            "full_name": "Dr. Raj Patel",
            "phone": "+1-555-0202",
            "organization": "Child Development Center"
        },
        {
            "email": "dr.williams@test.com",
            "password": "Doctor@123",
            "role": UserRole.PSYCHOLOGIST,
            "full_name": "Dr. Amanda Williams",
            "phone": "+1-555-0203",
            "organization": "Educational Psychology Associates"
        },

        # Admin Accounts
        {
            "email": "admin1@test.com",
            "password": "Admin@123",
            "role": UserRole.ADMIN,
            "full_name": "System Administrator",
            "phone": "+1-555-0301",
            "organization": "EdPsych AI"
        },
        {
            "email": "admin2@test.com",
            "password": "Admin@123",
            "role": UserRole.ADMIN,
            "full_name": "Platform Manager",
            "phone": "+1-555-0302",
            "organization": "EdPsych AI"
        }
    ]

    async with AsyncSessionLocal() as session:
        created_count = 0
        skipped_count = 0

        for user_data in test_users:
            # Check if user already exists
            result = await session.execute(
                select(User).where(User.email == user_data["email"])
            )
            existing_user = result.scalar_one_or_none()

            if existing_user:
                print(f"[SKIP] {user_data['email']} - Already exists")
                skipped_count += 1
                continue

            # Create new user
            new_user = User(
                email=user_data["email"],
                password_hash=get_password_hash(user_data["password"]),
                role=user_data["role"],
                full_name=user_data["full_name"],
                phone=user_data["phone"],
                organization=user_data["organization"],
                is_active=True,
                is_verified=True
            )

            session.add(new_user)
            print(f"[OK] Created {user_data['role'].value}: {user_data['email']}")
            created_count += 1

        await session.commit()

    print("\n" + "=" * 60)
    print(f"TEST USER SEEDING COMPLETED")
    print("=" * 60)
    print(f"Created: {created_count} users")
    print(f"Skipped: {skipped_count} users (already exist)")
    print("\nTest accounts are ready to use!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed_test_users())
