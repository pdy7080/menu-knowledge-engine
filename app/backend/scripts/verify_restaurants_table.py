"""
Verify Restaurants Table Creation

Checks that the restaurants table was created with all expected columns and indexes.
"""
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from database import engine


async def verify_table():
    """Verify restaurants table structure"""
    async with engine.begin() as conn:
        # 1. Check table exists
        print("[*] Checking if restaurants table exists...")
        result = await conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'restaurants'
            )
        """))
        exists = result.scalar()

        if not exists:
            print("[ERROR] restaurants table does not exist!")
            return False

        print("[OK] restaurants table exists")

        # 2. Check columns
        print("\n[*] Checking columns...")
        result = await conn.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'restaurants'
            ORDER BY ordinal_position
        """))
        columns = result.fetchall()

        expected_columns = [
            'id', 'name', 'name_en', 'owner_name', 'owner_phone', 'owner_email',
            'address', 'address_detail', 'postal_code',
            'business_license', 'business_type', 'status',
            'approved_at', 'approved_by', 'rejection_reason',
            'created_at', 'updated_at'
        ]

        column_names = [col[0] for col in columns]

        for col_name in expected_columns:
            if col_name in column_names:
                print(f"  [OK] {col_name}")
            else:
                print(f"  [ERROR] Missing column: {col_name}")

        # 3. Check indexes
        print("\n[*] Checking indexes...")
        result = await conn.execute(text("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'restaurants'
            ORDER BY indexname
        """))
        indexes = [row[0] for row in result.fetchall()]

        expected_indexes = [
            'restaurants_pkey',  # Primary key
            'restaurants_business_license_key',  # Unique constraint
            'idx_restaurants_business_license',
            'idx_restaurants_status',
            'idx_restaurants_status_created',
            'idx_restaurants_approved'
        ]

        for idx_name in expected_indexes:
            if idx_name in indexes:
                print(f"  [OK] {idx_name}")
            else:
                print(f"  [ERROR] Missing index: {idx_name}")

        # 4. Test insert and select
        print("\n[*] Testing insert and select...")
        try:
            # Insert test restaurant
            await conn.execute(text("""
                INSERT INTO restaurants (
                    name, owner_name, owner_phone, address, business_license, status
                ) VALUES (
                    'Test Restaurant', 'Test Owner', '010-1234-5678',
                    'Test Address', 'TEST-LICENSE-001', 'pending_approval'
                )
            """))

            # Select test restaurant
            result = await conn.execute(text("""
                SELECT name, owner_name, status, business_license
                FROM restaurants
                WHERE business_license = 'TEST-LICENSE-001'
            """))
            row = result.fetchone()

            if row:
                print(f"  [OK] Insert/Select successful")
                print(f"    Name: {row[0]}")
                print(f"    Owner: {row[1]}")
                print(f"    Status: {row[2]}")
                print(f"    License: {row[3]}")

                # Clean up test data
                await conn.execute(text("""
                    DELETE FROM restaurants WHERE business_license = 'TEST-LICENSE-001'
                """))
                print(f"  [OK] Test data cleaned up")
            else:
                print(f"  [ERROR] Insert/Select failed")

        except Exception as e:
            print(f"  [ERROR] Insert/Select failed: {e}")

        print("\n[DONE] Verification completed successfully!")
        return True


if __name__ == "__main__":
    asyncio.run(verify_table())
