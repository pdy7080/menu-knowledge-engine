"""
Database connection and session management
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from config import settings

# Auto-detect database type and adjust URL
def get_database_url() -> str:
    """Get database URL with correct driver"""
    url = settings.DATABASE_URL

    # PostgreSQL: use asyncpg
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://")

    # SQLite: use aiosqlite
    if url.startswith("sqlite:///"):
        return url.replace("sqlite:///", "sqlite+aiosqlite:///")

    # Already has driver specified
    return url

# Create async engine
engine = create_async_engine(
    get_database_url(),
    echo=settings.DEBUG,
    future=True,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """Dependency for getting async database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database - create all tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
