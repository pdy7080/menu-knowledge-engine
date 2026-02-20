"""
Get menus with enriched content for test case selection
"""
import asyncio
from sqlalchemy import text
import sys
from pathlib import Path

# Path 설정
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR / "app" / "backend"))

from database import engine


async def get_enriched_menus():
    """Get menus with enriched content"""
    async with engine.begin() as conn:
        result = await conn.execute(
            text("""
                SELECT id, name_ko, name_en, content_completeness
                FROM canonical_menus
                WHERE content_completeness > 0
                ORDER BY content_completeness DESC
                LIMIT 10
            """)
        )
        rows = result.fetchall()

        print(f"Found {len(rows)} menus with enriched content\n")
        print(f"{'ID':<36} | {'Korean':<20} | {'English':<30} | Completeness")
        print("=" * 120)

        for row in rows:
            print(f"{row[0]} | {row[1]:<20} | {row[2]:<30} | {row[3]}%")


if __name__ == "__main__":
    asyncio.run(get_enriched_menus())
