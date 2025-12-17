from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from models.question import Question as QuestionORM, Topic as TopicORM
from schemas.question import (
    QuestionCreate, Question as QuestionSchema,
    TopicCreate, TopicRead as TopicSchema,
    QuestionFilters
)
from database.question import get_async_session, init_db, AsyncSessionLocal
from typing import List, Union
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from database.seed import seed_topics

# -----------------------------
# FastAPI setup
# -----------------------------
app = FastAPI(title="Quiz Service - Questions API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    """Initialize database and seed initial data"""
    await init_db()
    print("✅ Database initialized")

    async with AsyncSessionLocal() as session:
        await seed_topics(session)


# -----------------------------
# Topic CRUD Endpoints
# -----------------------------

# List all topics
@app.get("/topics/", response_model=list[TopicSchema])
async def get_topics(session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(TopicORM))
    return result.scalars().all()


# Create topic
@app.post("/topics/", response_model=TopicSchema)
async def create_topic(t: TopicCreate, session: AsyncSession = Depends(get_async_session)):
    new_topic = TopicORM(**t.dict())
    session.add(new_topic)
    await session.commit()
    await session.refresh(new_topic)
    return new_topic


# Delete topic by ID
@app.delete("/topics/{topic_id}")
async def delete_topic(topic_id: str, session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(TopicORM).where(TopicORM.id == topic_id))
    topic = result.scalar_one_or_none()
    if topic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")
    await session.delete(topic)
    await session.commit()
    return {"detail": "Topic deleted"}


# -----------------------------
# Question CRUD Endpoints
# -----------------------------

# Bulk create questions endpoint
@app.post("/questions/", response_model=List[QuestionSchema])
async def create_question(q: Union[QuestionCreate, List[QuestionCreate]], session: AsyncSession = Depends(get_async_session)):
    questions = q if isinstance(q, list) else [q]
    new_questions = [QuestionORM(**question.dict()) for question in questions]
    session.add_all(new_questions)
    await session.commit()
    for new_q in new_questions:
        await session.refresh(new_q)
    return new_questions


# List questions with filters
@app.get("/questions/", response_model=List[QuestionSchema])
async def get_questions(filters: QuestionFilters = Depends(), session: AsyncSession = Depends(get_async_session)):
    query = select(QuestionORM)
    if filters.topic_id:
        query = query.where(QuestionORM.topic_id == filters.topic_id)
    if filters.randomize:
        query = query.order_by(func.random())
    query = query.limit(filters.limit)
    result = await session.execute(query)
    return result.scalars().all()


# Get question by ID
@app.get("/questions/{question_id}", response_model=QuestionSchema)
async def get_question(question_id: str, session: AsyncSession = Depends(get_async_session)):
    q = await session.get(QuestionORM, question_id)
    if not q:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    return q


# Update question
@app.put("/questions/{question_id}", response_model=QuestionSchema)
async def update_question(question_id: str, q_update: QuestionCreate, session: AsyncSession = Depends(get_async_session)):
    q = await session.get(QuestionORM, question_id)
    if not q:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    if q_update.topic_id != q.topic_id:
        topic = await session.get(TopicORM, q_update.topic_id)
        if not topic:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Topic with id {q_update.topic_id} not found")
    for key, value in q_update.dict().items():
        setattr(q, key, value)
    q.updated_at = datetime.utcnow()
    await session.commit()
    await session.refresh(q)
    return q


# Delete question
@app.delete("/questions/{question_id}")
async def delete_question(question_id: str, session: AsyncSession = Depends(get_async_session)):
    q = await session.get(QuestionORM, question_id)
    if not q:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    await session.delete(q)
    await session.commit()
    return {"detail": "Question deleted"}
