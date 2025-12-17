from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from models.question import Question as QuestionORM, Topic as TopicORM
from schemas.question import (
    QuestionCreate, Question as QuestionSchema,
    TopicCreate, TopicRead as TopicSchema,
    QuestionFilters
)
from database.question import get_async_session, init_db
from typing import List
from datetime import datetime

# -----------------------------
# FastAPI setup
# -----------------------------
app = FastAPI(title="Quiz Service - Questions API")

@app.on_event("startup")
async def on_startup():
    """Initialize database tables on application startup"""
    await init_db()
    print("✅ Database initialized")

# -----------------------------
# Topic CRUD Endpoints
# -----------------------------

# List all topics
@app.get("/topics/", response_model=List[TopicSchema])
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


# Delete topic by ID (REFERENCE IMPLEMENTATION)
@app.delete("/topics/{topic_id}")
async def delete_topic(
    topic_id: str,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Delete a topic by ID.

    Note: This will also delete all questions associated with this topic
    if cascade delete is configured on the relationship.
    """
    result = await session.execute(
        select(TopicORM).where(TopicORM.id == topic_id)
    )
    topic = result.scalar_one_or_none()

    if topic is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found"
        )

    await session.delete(topic)
    await session.commit()
    return {"detail": "Topic deleted"}


# -----------------------------
# Question CRUD Endpoints
# -----------------------------

# Create question (UPDATED - now requires valid topic_id)
@app.post("/questions/", response_model=QuestionSchema)
async def create_question(
    q: QuestionCreate,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Create a new question.

    Now validates that topic_id references an existing topic.
    """
    # Verify topic exists
    topic = await session.get(TopicORM, q.topic_id)
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic with id {q.topic_id} not found"
        )

    new_q = QuestionORM(**q.dict())
    session.add(new_q)
    await session.commit()
    await session.refresh(new_q)
    return new_q


# TODO: Implement LIST QUESTIONS with filters endpoint
# GET /questions/
# - Accept QuestionFilters as dependency: filters: QuestionFilters = Depends()
# - Build base query: select(QuestionORM)
# - Apply filter if topic_id provided: .where(QuestionORM.topic_id == filters.topic_id)
# - Apply randomize if requested: .order_by(func.random())
# - Apply limit: .limit(filters.limit)
# - Execute and return results


# Get question by ID (REFERENCE - unchanged from 3.1)
@app.get("/questions/{question_id}", response_model=QuestionSchema)
async def get_question(
    question_id: str,
    session: AsyncSession = Depends(get_async_session)
):
    """Retrieve a single question by ID"""
    q = await session.get(QuestionORM, question_id)
    if not q:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    return q


# Update question (REFERENCE - unchanged from 3.1)
@app.put("/questions/{question_id}", response_model=QuestionSchema)
async def update_question(
    question_id: str,
    q_update: QuestionCreate,
    session: AsyncSession = Depends(get_async_session)
):
    """Update an existing question"""
    q = await session.get(QuestionORM, question_id)
    if not q:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )

    # Verify new topic exists if topic_id is being changed
    if q_update.topic_id != q.topic_id:
        topic = await session.get(TopicORM, q_update.topic_id)
        if not topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Topic with id {q_update.topic_id} not found"
            )

    for key, value in q_update.dict().items():
        setattr(q, key, value)

    q.updated_at = datetime.utcnow()
    await session.commit()
    await session.refresh(q)
    return q


# Delete question (REFERENCE - unchanged from 3.1)
@app.delete("/questions/{question_id}")
async def delete_question(
    question_id: str,
    session: AsyncSession = Depends(get_async_session)
):
    """Delete a question by ID"""
    q = await session.get(QuestionORM, question_id)
    if not q:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )

    await session.delete(q)
    await session.commit()
    return {"detail": "Question deleted"}
