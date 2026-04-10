import asyncio
from sqlalchemy import text
from app.core.database import engine

async def get_users():
    async with engine.begin() as conn:
        result = await conn.execute(
            text("SELECT email, role FROM users WHERE role = 'PSYCHOLOGIST' OR role = 'PARENT' LIMIT 5")
        )
        rows = result.fetchall()
        if rows:
            print("\nAvailable users:")
            print("-" * 50)
            for row in rows:
                print(f"Email: {row[0]}")
                print(f"Role: {row[1]}")
                print("-" * 50)
        else:
            print('No users found')

asyncio.run(get_users())
