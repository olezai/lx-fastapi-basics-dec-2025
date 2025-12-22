from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
import uuid

class QuizRequest(BaseModel):
    name: str = Field(..., example = "History recap")

    #Question filter
    topic_id: str = Field(..., example="insert_topic_id", description = "Use http://question-srv:8000/topics/ to get topic ids.")    
    limit: int = Field(10, ge=1, le=100)
    randomize: bool = True

    #Rule settings
    time_limit_seconds: Optional[int] = 900
    passing_ratio: Optional[float] = 0.7
    number_of_attempts: Optional[int] = Field(None, example=None,  nullable=True, description="None for unlimited")

class QuizFilter(BaseModel):
    user_id: Optional[str] = None
    topic_id: Optional[str] = None
    is_active: Optional[bool] = None

    min_question_count: Optional[int] = Field(None, ge=1, le=100)
    max_question_count: Optional[int] = Field(None, ge=1, le=100)

class AnswerOption(BaseModel):
    num: int
    text: str

class QuizQuestion(BaseModel):
    id: str
    name: str
    quiz_id: str
    question_id: str
    question: str
    options: List[AnswerOption]
    # We omit 'correct_option' and 'explanation' from the response to the user during the active quiz.
    order_index: int
    
    model_config = ConfigDict(from_attributes=True)

class QuestionForClient(BaseModel):
    id: str
    question: str
    options: List[AnswerOption]
    order_index: int
    
    model_config = ConfigDict(from_attributes=True)

class Quiz(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    user_id: str

    topic_id: str
    topic_name: str
    question_count: int
    passing_ratio: float
    time_limit_seconds: Optional[int]
    number_of_attempts: Optional[int]

    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

class QuizDetails(Quiz):
    questions: List[QuizQuestion] = []

class QuizSessionFilter(BaseModel):
    user_id: str | None = Field(None)
    quiz_id: str | None = Field(None)
    is_active: bool | None = Field(None)

class QuizSession(BaseModel):
    id: str
    quiz_id: str
    user_id: str
    
    attempt_number: int
    question_progress_index: int #old name: current_question_index
    question_count: int
    score: int
    wrong_answers: Optional[int]
    unanswered_questions: Optional[int]
    time_limit_seconds: Optional[int]
    is_active: bool
    
    started_at: datetime
    completed_at: Optional[datetime]
    completion_details: Optional[str]

class AnswerSubmitRequest(BaseModel):
    selected_option: int = Field(..., ge=0, description="Index of selected option")
    
    class Config:
        json_schema_extra = {
            "example": {
                "selected_option": 2
            }
        }

class Answer(BaseModel):
    
    id: str
    quiz_session_id: str
    quiz_question_id: str

    selected_option: int
    is_correct: Optional[bool]

    answered_at: datetime
    updated_at: Optional[datetime]
    submitted_at: Optional[datetime]
    revision_count: int
    attempt_number: int

class QuizSessionDetails(QuizSession):
    answers: List[Answer]

# Response after quiz submission
class QuizSessionSummary(BaseModel):
    id: str
    quiz_id: str
    score: int
    question_count: int
    score_percentage: float
    score: int
    wrong_answers: int
    unanswered_questions: int
    time_taken_seconds: int    
    completed_at: datetime
    completion_details: str
    passed: bool
    
    class Config:
        from_attributes = True

# Individual question result for detailed review
class QuestionResultDetail(BaseModel):
    question_id: str
    question_text: str
    user_answer: Optional[int]
    correct_answer: int
    is_correct: Optional[bool]
    is_answered: bool

# Detailed results including per-question breakdown
class DetailedQuizResults(QuizSessionSummary):
    questions: List[QuestionResultDetail]