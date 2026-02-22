"""
Drop Restaurants Table

For clean re-migration during development.
"""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from database import engine


async def drop_table():
    """Drop restaurants table and enum type"""
    async with engine.begin() as conn:
        print("[*] Dropping restaurants table...")
        await conn.execute(text("DROP TABLE IF EXISTS restaurants CASCADE"))
        print("[OK] Table dropped")

        print("[*] Dropping restaurantstatus enum type...")
        await conn.execute(text("DROP TYPE IF EXISTS restaurantstatus CASCADE"))
        print("[OK] Enum type dropped")

    print("\n[DONE] Clean drop completed")


if __name__ == "__main__":
    asyncio.run(drop_table())
