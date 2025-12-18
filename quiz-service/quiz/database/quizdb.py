import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from models.quizmodel import Base

sys.stdout.reconfigure(line_buffering=True)

# Use asyncpg driver
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://svc_usr:svc_pwd@service-db:5432/svc_db")

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=False, future=True)

# Create session factory
AsyncSessionLocal = sessionmaker(
    bind = engine,
    class_ = AsyncSession,
    autoflush = False,
    autocommit = False,
    expire_on_commit = False,
)

# Initialize DB (async)
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Dependency for FastAPI
async def get_async_session():
    async with AsyncSessionLocal() as session:
        yield session

async def reset_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)