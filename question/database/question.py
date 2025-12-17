import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from models.question import Base

sys.stdout.reconfigure(line_buffering=True)

# Database connection string
# Format: postgresql+asyncpg://user:password@host:port/database
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://quest_usr:quest_pswd@question-db:5432/questions_db"
)

# Create async engine
# - echo=True would log all SQL statements (useful for debugging)
# - future=True uses SQLAlchemy 2.0 style
engine = create_async_engine(DATABASE_URL, echo=False, future=True)

# Create session factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession, # - AsyncSession: async version of Session
    autoflush=False, # - autoflush=False: don't auto-flush before queries
    autocommit=False, # - autocommit=False: require explicit commits
    expire_on_commit=False, # - expire_on_commit=False: keep objects usable after commit (important for FastAPI)
)

# Initialize database tables
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# FastAPI dependency for database sessions
async def get_async_session():
    async with AsyncSessionLocal() as session:
        yield session
