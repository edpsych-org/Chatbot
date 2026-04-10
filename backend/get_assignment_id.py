import asyncio
from sqlalchemy import text
from app.core.database import engine

async def get_id():
    async with engine.begin() as conn:
        result = await conn.execute(
            text('SELECT id FROM assessment_assignments ORDER BY assigned_at DESC LIMIT 1')
        )
        row = result.fetchone()
        if row:
            print(row[0])
        else:
            print('No assignments found')

asyncio.run(get_id())
