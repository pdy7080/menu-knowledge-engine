"""
Apply performance optimization indexes to database
"""
import psycopg2
import sys

def apply_indexes():
    try:
        # Connect to database
        conn = psycopg2.connect('postgresql://menu_admin:menu_dev_2025@localhost/menu_knowledge_db')
        conn.autocommit = True
        cursor = conn.cursor()

        # Read SQL file
        with open('app/backend/migrations/performance_optimization.sql', 'r', encoding='utf-8') as f:
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

        print("🔧 Applying performance indexes...")

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

                # Show progress for CREATE INDEX
                if 'CREATE INDEX' in statement.upper():
                    # Extract index name
                    if 'IF NOT EXISTS' in statement.upper():
                        index_name = statement.upper().split('IF NOT EXISTS')[1].split('ON')[0].strip()
                    else:
                        index_name = statement.upper().split('INDEX')[1].split('ON')[0].strip()
                    print(f"  ✅ Created index: {index_name}")
                elif 'ANALYZE' in statement.upper() and 'VACUUM' not in statement.upper():
                    table_name = statement.split('ANALYZE')[1].strip()
                    print(f"  📊 Analyzed: {table_name}")
                elif 'VACUUM' in statement.upper():
                    if 'VACUUM ANALYZE' in statement.upper():
                        table_name = statement.upper().split('VACUUM ANALYZE')[1].strip()
                        print(f"  🧹 Vacuumed & Analyzed: {table_name}")
                    else:
                        table_name = statement.upper().split('VACUUM')[1].strip()
                        print(f"  🧹 Vacuumed: {table_name}")

            except psycopg2.Error as e:
                # Ignore "already exists" errors
                if 'already exists' in str(e):
                    if 'CREATE INDEX' in statement.upper():
                        if 'IF NOT EXISTS' in statement.upper():
                            index_name = statement.upper().split('IF NOT EXISTS')[1].split('ON')[0].strip()
                        else:
                            index_name = statement.upper().split('INDEX')[1].split('ON')[0].strip()
                        print(f"  ⚠️  Index already exists: {index_name}")
                else:
                    print(f"  ❌ Error: {e}")

        cursor.close()
        conn.close()

        print(f"\n✅ Performance optimization complete!")
        print(f"   Executed: {executed} statements")
        print(f"   Skipped: {skipped} verification queries")

        return True

    except Exception as e:
        print(f"❌ Error applying indexes: {e}")
        return False

if __name__ == "__main__":
    success = apply_indexes()
    sys.exit(0 if success else 1)
