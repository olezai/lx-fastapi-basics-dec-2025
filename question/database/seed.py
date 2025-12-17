from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.question import Topic

# TODO: Implement seed_topics function
# This function should:
# 1. Accept AsyncSession as parameter
# 2. Define default_topics list: ["General", "History", "Pets"]
# 3. For each topic name:
#    - Check if topic exists: select(Topic).where(Topic.name == name)
#    - If not exists, create new Topic with that name
# 4. Commit changes

async def seed_topics(session: AsyncSession):
    default_topics = ["General", "History", "Pets"]

    for name in default_topics:
        result = await session.execute(select(Topic).where(Topic.name == name))
        existing_topic = result.scalar_one_or_none()
        if not existing_topic:
            new_topic = Topic(name=name)
            session.add(new_topic)

    await session.commit()