from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func, update
from database.quizdb import get_async_session, init_db, reset_db
from models.quizmodel import Quiz as QuizORM, QuizQuestion as QuizQuestionORM, QuizSession as QuizSessionORM, Answer as AnswerORM
from schema.quizschema import QuizRequest as QuizRequestSchema, Quiz as QuizSchema, QuizDetails as QuizDetailsSchema, QuizFilter, AnswerSubmitRequest, QuestionForClient, QuizSession as QuizSessionSchema, QuizSessionFilter, QuizSessionDetails
from schema.quizschema import QuizSessionSummary as QuizSummary
from typing import List
from datetime import datetime
import httpx
import os

# Create FastAPI application instance
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


async def fetch_questions_from_service(request: QuizRequestSchema) -> List[dict]:
    """
    Fetch questions from question-service (inter-service HTTP call).
    
    Implements API composition pattern from theory section 6.
    """
    payload = request.model_dump(exclude={"name", "time_limit_seconds", "passing_ratio", "number_of_attempts"})
    clean_payload = filter_none(payload)
    clean_payload["is_public"] = True

    url = httpx.URL(QUESTIONS_URL, params=clean_payload)

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


def filter_none(d: dict) -> dict:
    """Remove None values from dict (for query params)"""
    return {k: v for k, v in d.items() if v is not None}

def get_current_user():
    return "1"

async def __get_q_session( 
        session_id: str,
        current_user: str,
        db: AsyncSession,
        require_active: bool = False,
        get_details: bool = False,
    ) -> QuizSessionORM:
    stmt = (
        select(QuizSessionORM)
        .filter(
            QuizSessionORM.id == session_id,
            QuizSessionORM.user_id == current_user,
        )
    )

    if get_details:
        stmt = stmt.options(
            selectinload(QuizSessionORM.quiz),
            selectinload(QuizSessionORM.answers),
            selectinload(QuizSessionORM.quiz).selectinload(QuizORM.questions)
        )

    result = await db.execute(stmt)
    qsession = result.scalar_one_or_none()

    if not qsession:
        raise HTTPException(status_code=404, detail="Quiz session not found")

    if require_active and not qsession.is_active:
        raise HTTPException(status_code=400, detail="Quiz session inactive or already submitted")

    return qsession

async def get_quiz_session_summary(
    session_id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> QuizSessionORM:
    return await __get_q_session(session_id, current_user, db)

async def get_quiz_session(
    session_id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> QuizSessionORM:
    return await __get_q_session(session_id, current_user, db, get_details=True)

async def get_active_quiz_session(
    session_id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
) -> QuizSessionORM:

    return await __get_q_session(session_id, current_user, db, require_active=True, get_details=True)

@app.on_event("startup")
async def on_startup():
    await init_db()

@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    
    return JSONResponse(
        status_code=409,
        content={
            "detail": "Data conflict occurred. Please retry your request.",
            "error_type": "integrity_error"
        }
    )

# Create quiz (caches questions from question-service)
@app.post("/quizzes/")
async def create_quiz(
    request: QuizRequestSchema,
    current_user: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Create a new quiz by fetching questions from question-service.

    This endpoint demonstrates the API composition pattern:
    1. Fetch questions from question-service (inter-service call)
    2. Create quiz template in our database
    3. Cache question snapshots (prevents changes affecting active quizzes)
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
    #add required fields for Quiz session
    q_data_dict['user_id'] = current_user
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
    await session.refresh(quiz)   # ensures quiz.id and timestamps are available
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
    """Delete quiz and all cached questions (cascade) - only if no sessions exist"""
    qz = await session.get(QuizORM, quiz_id, options=(selectinload(QuizORM.questions),))
    if not qz:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")

    # Check if quiz has any sessions (prevent deletion if sessions exist)
    result = await session.scalar(
        select(func.count(QuizSessionORM.id)).where(QuizSessionORM.quiz_id == quiz_id)
    )
    session_count = result or 0

    if session_count > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot delete quiz with existing sessions. Found {session_count} session(s). Delete sessions first."
        )

    await session.delete(qz)
    await session.commit()
    return {"detail": "Quiz deleted"}

@app.post("/quizzes/{quiz_id}/start")
async def start_quiz_session(
    quiz_id: str,
    current_user: str = Depends(get_current_user),
    session : AsyncSession = Depends(get_async_session)
):
    result = await session.execute(
        select(QuizORM).where(QuizORM.id == quiz_id)
    )
    quiz = result.scalar_one_or_none()
    # quiz = session.query(QuizORM).filter(QuizORM.id == quiz_id).first()
    
    # Count user's previous attempts for this quiz
    result = await session.scalar(
        select(func.count(QuizSessionORM.id)).where(
            QuizSessionORM.quiz_id == quiz_id,
            QuizSessionORM.user_id == current_user
        )
    )
    previous_attempts = result or 0
    
    # Check if user exceeded max attempts
    if quiz.number_of_attempts is not None and quiz.number_of_attempts !=0 and previous_attempts >= quiz.number_of_attempts:
        raise HTTPException(
            status_code=403,
            detail=f"Maximum attempts ({quiz.number_of_attempts}) reached for this quiz"
        )
    
    # Create new session
    qs = QuizSessionORM(
        quiz_id=quiz_id,
        user_id=current_user,
        attempt_number=previous_attempts + 1,  # Store which attempt this is
        question_count=quiz.question_count
    )
    
    session.add(qs)
    await session.commit()
    await session.refresh(qs)
    
    return qs

#get quiz sessions
@app.get("/sessions/", response_model=list[QuizSessionSchema])
async def list_quiz_sessions(
    filters: QuizSessionFilter = Depends(),
    session: AsyncSession = Depends(get_async_session)
):
    query = select(QuizSessionORM)

    if filters.user_id:
        query = query.where(QuizSessionORM.user_id == filters.user_id)
    if filters.quiz_id:
        query = query.where(QuizSessionORM.quiz_id == filters.quiz_id)
    if filters.is_active is not None:
        query = query.where(QuizSessionORM.is_active == filters.is_active)

    result = await session.scalars(query)
    return result.all()

#get quiz session details
@app.get("/sessions/{session_id}", response_model=QuizSessionDetails)
async def get_quiz_session(qsession: QuizSessionORM = Depends(get_quiz_session)):
    return qsession

#get submitted quiz session stats
@app.get("/sessions/{session_id}/stats", response_model=QuizSummary)
async def get_quiz_session_stats( qsession: QuizSessionORM = Depends(get_quiz_session_summary)):
    if qsession.is_active:
        raise HTTPException(
            status_code=400,
            detail=f"The quiz ({qsession.id}) is not submitted yet."
        )
    return qsession


# Delete quiz session (for testing/debugging)
@app.delete("/sessions/{session_id}")
async def delete_quiz_session(
    qsession: QuizSessionORM = Depends(get_quiz_session_summary),
    db: AsyncSession = Depends(get_async_session)
):
    """Delete a quiz session - useful for testing"""
    await db.delete(qsession)
    await db.commit()
    return {"detail": "Quiz session deleted"}


# Get next quiz question
@app.get("/sessions/{session_id}/questions/next", response_model=QuestionForClient)
async def get_next_question(
    qsession: QuizSessionORM = Depends(get_active_quiz_session),
    db: AsyncSession = Depends(get_async_session)
):
    
    if qsession.question_progress_index == qsession.question_count:
        raise HTTPException(status_code=204, detail="No more questions.")
    
    result = await db.execute(
        select(QuizQuestionORM).filter(
            QuizQuestionORM.quiz_id == qsession.quiz_id,
            QuizQuestionORM.order_index == qsession.question_progress_index
        )
    )
    q = result.scalar_one_or_none()
    
    if not q:
        raise HTTPException(status_code=404, detail=f"Failed to accure question index: {qsession.question_progress_index}")
    
    return q

# User can update their answer while quiz is not submitted
@app.put("/sessions/{session_id}/answers/{question_id}")
async def update_answer(
    session_id: str,
    question_id: str,
    new_answer: AnswerSubmitRequest,
    qsession: QuizSessionORM = Depends(get_active_quiz_session),
    session : AsyncSession = Depends(get_async_session)
):


    result = await session.execute(
        select(AnswerORM).filter(
        AnswerORM.quiz_session_id == session_id,
        AnswerORM.quiz_question_id == question_id
        )
    )
    answer = result.scalar_one_or_none()

    # Update or create answer
    if answer:
        answer.selected_option = new_answer.selected_option
        answer.revision_count += 1
        answer.updated_at = datetime.utcnow()
    else:
        answer = AnswerORM(
            quiz_session_id=session_id,
            quiz_question_id=question_id,
            selected_option=new_answer.selected_option,
            revision_count=0
        )
        session.add(answer)
    
    if qsession.question_progress_index < qsession.question_count:
        qsession.question_progress_index += 1
    
    # Commit all changes
    await session.commit()
    await session.refresh(answer)

    return answer

@app.post("/sessions/{session_id}/submit", response_model=QuizSummary)
async def submit_quiz(
    qsession: QuizSessionORM = Depends(get_active_quiz_session),
    db: AsyncSession = Depends(get_async_session)
):
    
    # Get all questions for this quiz
    result = await db.execute(
        select(QuizQuestionORM).where(
            QuizQuestionORM.quiz_id == qsession.quiz_id
        ).order_by(QuizQuestionORM.order_index)
    )
    questions = result.scalars().all()
    
    # Get all answers for this session
    result = await db.execute(
        select(AnswerORM).where(
            AnswerORM.quiz_session_id == qsession.id,
            AnswerORM.attempt_number == 1  # Exam-style, only attempt 1
        )
    )
    answers = result.scalars().all()
    
    # Create a map of question_id -> answer for quick lookup
    answer_map = {answer.quiz_question_id: answer for answer in answers}
    
    # Grade all answers
    correct_count = 0
    wrong_count = 0
    unanswered_count = 0
    
    for question in questions:
        answer = answer_map.get(question.id)
        
        if answer:
            # Check if answer is correct
            is_correct = (answer.selected_option == question.correct_option)
            
            # Update answer with correctness
            answer.is_correct = is_correct
            answer.graded_at = datetime.utcnow()
            
            if is_correct:
                correct_count += 1
            else:
                wrong_count += 1
        else:
            # Question not answered
            unanswered_count += 1
    
    # Update quiz session
    qsession.score = correct_count
    qsession.wrong_answers = wrong_count
    qsession.unanswered_questions = unanswered_count
    qsession.is_active = False
    qsession.completed_at = datetime.utcnow()
    qsession.completion_details = "completed"
    
    # Commit all changes
    await db.commit()
    await db.refresh(qsession)

    return qsession
    
@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/reset-data")
async def reset_data(secret: str):
    if secret != "supersecret":
        return {"error": "unauthorized"}
    await reset_db()
    return {"status": "database reset"}