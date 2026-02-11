"""
Apply missing columns migration to database
"""
import psycopg2
import sys

def apply_migration():
    try:
        # Connect to database
        conn = psycopg2.connect('postgresql://menu_admin:menu_dev_2025@localhost/menu_knowledge_db')
        conn.autocommit = True
        cursor = conn.cursor()

        # Read SQL file
        with open('app/backend/migrations/add_missing_columns.sql', 'r', encoding='utf-8') as f:
            sql_content = f.read()

        # Remove comments and split by semicolons
        lines = sql_content.split('\n')
        sql_lines = []
        for line in lines:
            # Remove inline comments
            if '--' in line:
                line = line[:line.index('--')]
            line = line.strip()
            if line:
                sql_lines.append(line)

        # Join and split by semicolon
        full_sql = ' '.join(sql_lines)
        statements = [s.strip() for s in full_sql.split(';') if s.strip()]

        print("🔧 Applying database migration...")
        print()

        executed = 0
        skipped = 0

        for statement in statements:
            # Skip SELECT statements (verification queries)
            if statement.upper().startswith('SELECT'):
                skipped += 1
                continue

            try:
                cursor.execute(statement + ';')
                executed += 1

                # Show progress
                if 'ALTER TABLE' in statement.upper() and 'ADD COLUMN' in statement.upper():
                    table_name = statement.upper().split('ALTER TABLE')[1].split('ADD COLUMN')[0].strip()
                    column_info = statement.upper().split('ADD COLUMN')[1].split('IF NOT EXISTS')
                    if len(column_info) > 1:
                        column_name = column_info[1].split()[0].strip()
                    else:
                        column_name = column_info[0].split()[0].strip()
                    print(f"  ✅ Added column {column_name} to {table_name}")
                elif 'UPDATE' in statement.upper():
                    table_name = statement.upper().split('UPDATE')[1].split('SET')[0].strip()
                    print(f"  📝 Updated {table_name}")

            except psycopg2.Error as e:
                # Ignore "already exists" errors
                if 'already exists' in str(e) or 'duplicate column' in str(e):
                    print(f"  ⚠️  Skipped (already exists)")
                else:
                    print(f"  ❌ Error: {e}")

        # Get verification results
        cursor.execute("""
            SELECT
                table_name,
                column_name,
                data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name IN ('scan_logs', 'menu_variants', 'shops')
              AND column_name IN (
                'status', 'matched_canonical_id', 'created_at',
                'canonical_menu_id', 'menu_name_ko', 'price_display', 'is_active', 'display_order',
                'shop_code'
              )
            ORDER BY table_name, column_name
        """)

        results = cursor.fetchall()

        cursor.close()
        conn.close()

        print()
        print(f"✅ Migration complete!")
        print(f"   Executed: {executed} statements")
        print(f"   Skipped: {skipped} verification queries")
        print()
        print("📋 Verified columns:")
        for table, column, dtype in results:
            print(f"   • {table}.{column} ({dtype})")

        return True

    except Exception as e:
        print(f"❌ Error applying migration: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = apply_migration()
    sys.exit(0 if success else 1)
