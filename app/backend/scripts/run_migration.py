"""
Run SQL Migration Script

Usage:
    python scripts/run_migration.py migrations/create_restaurants_table.sql
"""
import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from database import engine


async def run_migration(sql_file: str):
    """Execute SQL migration file"""
    # Read SQL file
    sql_path = Path(__file__).parent.parent / sql_file

    if not sql_path.exists():
        print(f"[ERROR] SQL file not found: {sql_path}")
        sys.exit(1)

    print(f"[*] Reading migration: {sql_path.name}")
    sql_content = sql_path.read_text(encoding='utf-8')

    # Remove comment lines (lines starting with --)
    lines = []
    for line in sql_content.split('\n'):
        stripped = line.strip()
        # Keep line if it's not a comment
        if not stripped.startswith('--'):
            lines.append(line)

    # Join lines and split by semicolons
    clean_sql = '\n'.join(lines)
    statements = [s.strip() for s in clean_sql.split(';') if s.strip()]

    print(f"[*] Found {len(statements)} SQL statements")

    # Execute migration
    success_count = 0
    skip_count = 0
    error_count = 0

    async with engine.begin() as conn:
        for i, statement in enumerate(statements, 1):
            try:
                # Show first 80 chars of statement
                preview = statement[:80].replace('\n', ' ')
                if len(statement) > 80:
                    preview += '...'
                print(f"  [{i}/{len(statements)}] {preview}")

                await conn.execute(text(statement))
                print(f"    [OK] Success")
                success_count += 1
            except Exception as e:
                # Ignore "already exists" errors
                error_msg = str(e).lower()
                if "already exists" in error_msg or "duplicate" in error_msg:
                    print(f"    [SKIP] Already exists")
                    skip_count += 1
                else:
                    print(f"    [ERROR] {str(e)[:200]}")
                    error_count += 1

    print(f"\n[DONE] Migration completed")
    print(f"  Success: {success_count}")
    print(f"  Skipped: {skip_count}")
    print(f"  Errors: {error_count}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/run_migration.py <sql_file>")
        print("Example: python scripts/run_migration.py migrations/create_restaurants_table.sql")
        sys.exit(1)

    asyncio.run(run_migration(sys.argv[1]))
