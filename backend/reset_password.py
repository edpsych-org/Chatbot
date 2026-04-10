import asyncio
import bcrypt
from sqlalchemy import text
from app.core.database import engine

async def reset_password():
    # Hash the password using bcrypt directly
    password = "password123"
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    new_hash = hashed.decode('utf-8')

    print(f"New password hash: {new_hash}")

    async with engine.begin() as conn:
        # Update all test users with the new hash
        result = await conn.execute(
            text("""
                UPDATE users
                SET password_hash = :new_hash
                WHERE email IN ('parent1@test.com', 'parent2@test.com', 'parent3@test.com', 'parent4@test.com', 'dr.smith@test.com')
            """),
            {"new_hash": new_hash}
        )
        print(f"Updated {result.rowcount} users")

asyncio.run(reset_password())
