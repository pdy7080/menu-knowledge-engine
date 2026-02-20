import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "app" / "backend"))

from database import AsyncSessionLocal
from models.canonical_menu import CanonicalMenu
from sqlalchemy import select, func


async def main():
    async with AsyncSessionLocal() as session:
        # Count total menus
        result = await session.execute(
            select(func.count()).select_from(CanonicalMenu)
        )
        total = result.scalar()

        # Count active menus
        result = await session.execute(
            select(func.count()).select_from(CanonicalMenu)
            .where(CanonicalMenu.status == "active")
        )
        active = result.scalar()

        print(f"Total canonical menus: {total}")
        print(f"Active canonical menus: {active}")
        print(f"Available for enrichment: {active}")


if __name__ == "__main__":
    asyncio.run(main())
