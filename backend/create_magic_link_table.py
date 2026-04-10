"""
Database migration script to create magic_link_tokens table
"""

import asyncio
from sqlalchemy import text
from app.core.database import engine


async def create_magic_link_table():
    """Create the magic_link_tokens table"""

    # Execute each SQL statement separately
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS magic_link_tokens (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        token VARCHAR(255) UNIQUE NOT NULL,
        expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
        used_at TIMESTAMP WITH TIME ZONE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    )
    """

    create_token_index = """
    CREATE INDEX IF NOT EXISTS ix_magic_link_tokens_token ON magic_link_tokens(token)
    """

    create_user_index = """
    CREATE INDEX IF NOT EXISTS ix_magic_link_tokens_user_id ON magic_link_tokens(user_id)
    """

    async with engine.begin() as conn:
        await conn.execute(text(create_table_sql))
        await conn.execute(text(create_token_index))
        await conn.execute(text(create_user_index))
        print("✅ magic_link_tokens table and indexes created successfully!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_magic_link_table())
