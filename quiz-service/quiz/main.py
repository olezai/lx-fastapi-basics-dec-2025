from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from models.quizmodel import Quiz as QuizORM, QuizQuestion as QuizQuestionORM
from schema.quizschema import QuizRequest as QuizRequestSchema, Quiz as QuizSchema, QuizDetails as QuizDetailsSchema, QuizFilter
from database.quizdb import get_async_session, init_db
from typing import List
import os

app = FastAPI(
    title="Quiz Service - Quiz API",
    description="Quiz application",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE = os.getenv("QUESTION_SERVICE_BASE_URL", "http://question-service:8000")

QUESTIONS_URL = f"{BASE}/questions/"
TOPICS_URL = f"{BASE}/topics/"


async def fetch_topic_from_service(topic_id: str) -> dict:
    """
    Fetch topic information from question-service.
    Used to get topic name for denormalization in Quiz model.
    """
    url = f"{TOPICS_URL}{topic_id}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=503,
            detail="Question service unavailable (timeout)"
        )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Question service unavailable (connection refused)"
        )
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Error from question service: {str(e)}"
        )


# TODO: Implement fetch_questions_from_service function
# This is the key inter-service communication pattern (API composition)
#
# Requirements:
# 1. Accept QuizRequestSchema as parameter
# 2. Extract question filters from request:
#    - topic_id, limit, randomize
#    - Add is_public=True (only fetch public questions)
# 3. Use httpx.AsyncClient() to make GET request to QUESTIONS_URL
#    - Pass filters as query params
#    - Set timeout=10.0
# 4. Handle errors:
#    - httpx.TimeoutException → HTTPException 503 "Question service unavailable"
#    - httpx.HTTPError → HTTPException 502 "Error from question service"
# 5. Return response.json() (list of question dicts)
#
# Reference pattern from theory section 6:
# async with httpx.AsyncClient(timeout=10.0) as client:
#     response = await client.get(url, params=params)
#     response.raise_for_status()
#     return response.json()


def filter_none(d: dict) -> dict:
    """Remove None values from dict (for query params)"""
    return {k: v for k, v in d.items() if v is not None}


@app.on_event("startup")
async def on_startup():
    await init_db()


# Create quiz (caches questions from question-service)
@app.post("/quizzes/")
async def create_quiz(
    request: QuizRequestSchema,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Create a new quiz by fetching questions from question-service.

    This endpoint demonstrates the API composition pattern:
    1. Fetch topic information for denormalization (get topic_name)
    2. Fetch questions from question-service (inter-service call)
    3. Create quiz template in our database
    4. Cache question snapshots (prevents changes affecting active quizzes)
    """
    # Fetch topic information to get topic_name (denormalization pattern)
    topic = await fetch_topic_from_service(request.topic_id)

    # Fetch questions from question service
    questions = await fetch_questions_from_service(request)

    # Validate we have enough questions
    if len(questions) == 0:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "No questions found matching criteria",
                "filters": {
                    "topic_id": request.topic_id,
                    "n_questions_requested": f"{request.limit}"
                }
            }
        )

    # Normalize number_of_attempts
    if request.number_of_attempts in (0, None):
        request.number_of_attempts = None

    # Create quiz template
    q_data_dict = request.model_dump(exclude={'limit', 'randomize'})
    q_data_dict['user_id'] = "1"  # move to DI in 4.2
    q_data_dict['question_count'] = len(questions)
    q_data_dict['topic_name'] = topic['name']  # Store denormalized topic name

    quiz = QuizORM(**q_data_dict)

    # Cache all questions (snapshot pattern - prevents changes affecting quiz)
    for idx, question in enumerate(questions):
        quiz_question = QuizQuestionORM(
            question_id=question["id"],
            name=question["name"],
            question=question["question"],
            options=question["options"],
            correct_option=question["correct_option"],
            explanation=question["explanation"],
            order_index=idx
        )
        quiz.questions.append(quiz_question)

    session.add(quiz)
    await session.commit()
    await session.refresh(quiz)

    return quiz


# List quizzes with filters
@app.get("/quizzes/", response_model=List[QuizSchema])
async def get_quiz(filters: QuizFilter = Depends(), session: AsyncSession = Depends(get_async_session)):
    """List quizzes with optional filters"""
    query = select(QuizORM)

    if filters.user_id:
        query = query.filter(QuizORM.user_id == filters.user_id)

    if filters.topic_id:
        query = query.filter(QuizORM.topic_id == filters.topic_id)

    if filters.is_active is not None:
        query = query.filter(QuizORM.is_active == filters.is_active)

    if filters.min_question_count and filters.max_question_count:
        if filters.min_question_count >= filters.max_question_count:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="min_question_count must be less than max_question_count"
            )

    if filters.min_question_count:
        query = query.filter(QuizORM.question_count >= filters.min_question_count)

    if filters.max_question_count:
        query = query.filter(QuizORM.question_count <= filters.max_question_count)

    result = await session.execute(query)
    quizzes = result.scalars().all()
    return quizzes


# Get quiz details with cached questions
@app.get("/quizzes/{quiz_id}", response_model=QuizDetailsSchema)
async def get_quiz_details(quiz_id: str, session: AsyncSession = Depends(get_async_session)):
    """Get quiz with all cached questions"""
    qz = await session.get(QuizORM, quiz_id, options=(selectinload(QuizORM.questions),))
    if not qz:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")
    return qz


# Delete quiz
@app.delete("/quizzes/{quiz_id}")
async def delete_quiz(quiz_id: str, session: AsyncSession = Depends(get_async_session)):
    """Delete quiz and all cached questions (cascade)"""
    qz = await session.get(QuizORM, quiz_id, options=(selectinload(QuizORM.questions),))
    if not qz:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")
    await session.delete(qz)
    await session.commit()
    return {"detail": "Quiz deleted"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}
