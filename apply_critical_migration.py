"""
Apply Critical Migration: Add Missing ScanLog Columns
Bug #1 Fix - 2026-02-11
"""
import psycopg2
import sys

def apply_critical_migration():
    """Add missing ScanLog columns to database"""

    print("🔧 Applying Critical Migration: ScanLog Columns")
    print("=" * 60)

    try:
        # Connect to database
        conn = psycopg2.connect(
            'postgresql://menu_admin:menu_dev_2025@localhost/menu_knowledge_db'
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # Define migration statements (explicit list to ensure order)
        statements = [
            ("menu_name_ko", "ALTER TABLE scan_logs ADD COLUMN IF NOT EXISTS menu_name_ko VARCHAR(200)"),
            ("confidence", "ALTER TABLE scan_logs ADD COLUMN IF NOT EXISTS confidence FLOAT"),
            ("evidences", "ALTER TABLE scan_logs ADD COLUMN IF NOT EXISTS evidences JSONB"),
            ("reviewed_at", "ALTER TABLE scan_logs ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMP WITH TIME ZONE"),
            ("review_notes", "ALTER TABLE scan_logs ADD COLUMN IF NOT EXISTS review_notes TEXT"),
        ]

        # Execute each statement
        for i, (col_name, statement) in enumerate(statements, 1):
            try:
                cursor.execute(statement)
                print(f"  ✅ [{i}/{len(statements)}] Added column: {col_name}")

            except Exception as e:
                error_msg = str(e)
                if 'already exists' in error_msg:
                    print(f"  ⏭️  [{i}/{len(statements)}] Column {col_name} already exists, skipping")
                else:
                    print(f"  ❌ [{i}/{len(statements)}] Error adding {col_name}: {e}")
                    raise

        cursor.close()
        conn.close()

        print("=" * 60)
        print("✅ Critical Migration Complete!")
        print()
        print("📋 Added Columns:")
        print("  - menu_name_ko (VARCHAR 200)")
        print("  - confidence (FLOAT)")
        print("  - evidences (JSONB)")
        print("  - reviewed_at (TIMESTAMP WITH TIME ZONE)")
        print("  - review_notes (TEXT)")

        return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False


if __name__ == "__main__":
    success = apply_critical_migration()
    sys.exit(0 if success else 1)
