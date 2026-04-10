import asyncio
from app.core.database import engine
from sqlalchemy import text

async def check():
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"))
        tables = result.fetchall()
        print("All tables in database:")
        for table in tables:
            print(f"  - {table[0]}")

        print("\nChecking for student_guardians table:")
        result = await conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename='student_guardians'"))
        sg_table = result.fetchone()
        if sg_table:
            print("✓ student_guardians table EXISTS")
        else:
            print("✗ student_guardians table DOES NOT EXIST")

asyncio.run(check())
