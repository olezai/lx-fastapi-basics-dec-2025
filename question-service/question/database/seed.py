from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.question import Topic as TopicORM


async def seed_topics(session: AsyncSession):
    """
    Seed the database with default topics.

    This function is idempotent - it can be run multiple times
    without creating duplicate topics.
    """
    default_topics = ["General", "History", "Pets"]

    for name in default_topics:
        # Check if topic already exists
        existing = await session.execute(
            select(TopicORM).where(TopicORM.name == name)
        )
        if existing.scalar_one_or_none() is None:
            # Topic doesn't exist, create it
            session.add(TopicORM(name=name))

    await session.commit()
    print(f"✅ Seeded {len(default_topics)} default topics")
