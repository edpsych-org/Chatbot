"""
Database Migration Runner
Executes SQL migration files against the PostgreSQL database
"""

import asyncio
import sys
import os
from pathlib import Path
from sqlalchemy import text

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

from app.core.database import engine
from app.core.config import settings


async def run_migration(migration_file: str):
    """
    Run a single SQL migration file

    Args:
        migration_file: Path to the SQL migration file
    """
    migration_path = Path(migration_file)

    if not migration_path.exists():
        print(f"[ERROR] Migration file not found: {migration_file}")
        return False

    print(f"\n[*] Running migration: {migration_path.name}")
    print(f"[*] Database: {settings.DATABASE_URL.split('@')[-1]}")
    print("=" * 60)

    try:
        # Read migration file
        with open(migration_path, 'r') as f:
            sql_content = f.read()

        # Execute migration
        async with engine.begin() as conn:
            # Remove comment lines first
            lines = sql_content.split('\n')
            cleaned_lines = [line for line in lines if not line.strip().startswith('--')]
            cleaned_sql = '\n'.join(cleaned_lines)

            # Split by semicolons to execute statements separately
            statements = [s.strip() for s in cleaned_sql.split(';') if s.strip()]

            for i, statement in enumerate(statements, 1):
                if statement:
                    print(f"\n[*] Executing statement {i}/{len(statements)}...")
                    await conn.execute(text(statement))
                    print(f"[OK] Statement {i} executed successfully")

        print("\n" + "=" * 60)
        print(f"[SUCCESS] Migration completed successfully: {migration_path.name}")
        return True

    except Exception as e:
        print("\n" + "=" * 60)
        print(f"[ERROR] Migration failed: {str(e)}")
        return False


async def run_all_migrations():
    """Run all migrations in the migrations directory"""
    migrations_dir = Path(__file__).parent / "migrations"

    if not migrations_dir.exists():
        print("[ERROR] Migrations directory not found")
        return False

    # Get all .sql files sorted by name
    migration_files = sorted(migrations_dir.glob("*.sql"))

    if not migration_files:
        print("[INFO] No migration files found")
        return True

    print(f"\n[*] Found {len(migration_files)} migration(s) to run")

    success_count = 0
    for migration_file in migration_files:
        success = await run_migration(str(migration_file))
        if success:
            success_count += 1
        else:
            print(f"\n[ERROR] Stopping migration process due to error in: {migration_file.name}")
            break

    print("\n" + "=" * 60)
    print(f"[SUMMARY] Migration Summary: {success_count}/{len(migration_files)} successful")
    return success_count == len(migration_files)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run specific migration file
        migration_file = sys.argv[1]
        success = asyncio.run(run_migration(migration_file))
    else:
        # Run all migrations
        success = asyncio.run(run_all_migrations())

    sys.exit(0 if success else 1)
