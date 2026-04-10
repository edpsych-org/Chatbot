"""
Create Hybrid Chat Tables Migration Script
Creates tables for the hybrid chatbot system
"""

import asyncio
import asyncpg
from sqlalchemy import text
from app.core.database import engine


async def create_chat_tables():
    """Create chat_sessions, chat_messages, flow_definitions, conversation_templates tables"""

    async with engine.begin() as conn:
        print("Creating hybrid chat tables...")

        # Create ENUM types first
        print("Creating ENUM types...")

        await conn.execute(text("""
            DO $$ BEGIN
                CREATE TYPE chatsessionstatus AS ENUM ('active', 'paused', 'completed', 'abandoned');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """))

        await conn.execute(text("""
            DO $$ BEGIN
                CREATE TYPE messagerole AS ENUM ('user', 'bot', 'system');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """))

        await conn.execute(text("""
            DO $$ BEGIN
                CREATE TYPE messagetype AS ENUM ('text', 'mcq_choice', 'adaptive_question', 'system_message');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """))

        print("ENUM types created successfully!")

        # Create chat_sessions table
        print("Creating chat_sessions table...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                assignment_id UUID NOT NULL REFERENCES assessment_assignments(id) ON DELETE CASCADE,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                user_type VARCHAR(50) NOT NULL,
                status VARCHAR(50) DEFAULT 'active',
                flow_type VARCHAR(100) NOT NULL,
                current_step INTEGER DEFAULT 0,
                current_node_id VARCHAR(100),
                context_data JSONB DEFAULT '{}'::jsonb,
                started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                last_interaction_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP WITH TIME ZONE,
                duration_minutes INTEGER,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # Create chat_messages table
        print("Creating chat_messages table...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
                role VARCHAR(50) NOT NULL,
                message_type VARCHAR(50) NOT NULL,
                content TEXT NOT NULL,
                message_metadata JSONB DEFAULT '{}'::jsonb,
                intent_classification JSONB,
                generation_source VARCHAR(50),
                generation_metadata JSONB,
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # Create flow_definitions table
        print("Creating flow_definitions table...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS flow_definitions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                flow_id VARCHAR(100) UNIQUE NOT NULL,
                flow_name VARCHAR(255) NOT NULL,
                flow_type VARCHAR(50) NOT NULL,
                version VARCHAR(50) NOT NULL,
                flow_data JSONB NOT NULL,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # Create conversation_templates table
        print("Creating conversation_templates table...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS conversation_templates (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                template_name VARCHAR(255) NOT NULL,
                template_type VARCHAR(50) NOT NULL,
                category VARCHAR(100),
                prompt_template TEXT NOT NULL,
                variables JSONB DEFAULT '[]'::jsonb,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # Create indexes
        print("Creating indexes...")
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_chat_sessions_assignment
            ON chat_sessions(assignment_id)
        """))

        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_chat_sessions_user
            ON chat_sessions(user_id)
        """))

        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_chat_sessions_status
            ON chat_sessions(status)
        """))

        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_chat_messages_session
            ON chat_messages(session_id)
        """))

        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_chat_messages_timestamp
            ON chat_messages(timestamp)
        """))

        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_flow_definitions_flow_id
            ON flow_definitions(flow_id)
        """))

        print("[SUCCESS] All hybrid chat tables created successfully!")
        print("\nTables created:")
        print("  - chat_sessions")
        print("  - chat_messages")
        print("  - flow_definitions")
        print("  - conversation_templates")
        print("\nIndexes created:")
        print("  - idx_chat_sessions_assignment")
        print("  - idx_chat_sessions_user")
        print("  - idx_chat_sessions_status")
        print("  - idx_chat_messages_session")
        print("  - idx_chat_messages_timestamp")
        print("  - idx_flow_definitions_flow_id")


if __name__ == "__main__":
    print("=== Hybrid Chat Tables Migration ===\n")
    asyncio.run(create_chat_tables())
    print("\nMigration complete!")
