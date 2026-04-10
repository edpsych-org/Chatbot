"""
Database Reset Script
Drops all tables and recreates them
"""

import asyncio
from sqlalchemy import text
from app.core.database import engine, Base
from app.models.user import User
from app.models.student import Student
from app.models.assessment import AssessmentSession, ChatbotQuestion, ChatbotAnswer
from app.models.assignment import AssessmentAssignment


async def reset_database():
    """Drop all tables and recreate them"""
    print("=" * 50)
    print("DATABASE RESET SCRIPT")
    print("=" * 50)

    async with engine.begin() as conn:
        print("\n[1/4] Dropping all existing tables with CASCADE...")
        # Use CASCADE to drop all dependent objects
        await conn.execute(text("""
            DO $$ DECLARE
                r RECORD;
            BEGIN
                FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                    EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                END LOOP;
            END $$;
        """))
        print("[OK] All tables dropped successfully")

        print("\n[2/4] Dropping all existing sequences...")
        await conn.execute(text("""
            DO $$ DECLARE
                r RECORD;
            BEGIN
                FOR r IN (SELECT sequence_name FROM information_schema.sequences WHERE sequence_schema = 'public') LOOP
                    EXECUTE 'DROP SEQUENCE IF EXISTS ' || quote_ident(r.sequence_name) || ' CASCADE';
                END LOOP;
            END $$;
        """))
        print("[OK] All sequences dropped successfully")

        print("\n[3/4] Creating all tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("[OK] All tables created successfully")

        print("\n[4/4] Verifying database structure...")
        result = await conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))
        tables = result.fetchall()

        print(f"[OK] Database has {len(tables)} tables:")
        for table in tables:
            print(f"  - {table[0]}")

    print("\n" + "=" * 50)
    print("DATABASE RESET COMPLETED SUCCESSFULLY")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Run: python seed_questions.py (to add assessment questions)")
    print("2. Start the backend server")
    print("3. Register new users and test the application")
    print()


if __name__ == "__main__":
    asyncio.run(reset_database())
