from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, Boolean, Null, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class Quiz(Base):
    __tablename__ = "quizzes"
    
    # Primary identification
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    user_id = Column(String, nullable=False, index=True)
    
    # Quiz configuration
    topic_id = Column(String, nullable=False)    
    topic_name = Column(String, nullable=False)  # Denormalized for API performance
    question_count = Column(Integer, nullable=False)
    passing_ratio = Column(Float, nullable=False) # e.g. 0.7 for 70%
    time_limit_seconds = Column(Integer, nullable=True) # e.g., 1800 for 30 minutes
    number_of_attempts = Column(Integer, nullable=True, default=None) #max number of attempts (per user)
   
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, nullable=True)

  # Relationships 
    questions = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan")
    sessions = relationship("QuizSession", back_populates="quiz")

class QuizQuestion(Base):
    __tablename__ = "quiz_questions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    quiz_id = Column(String, ForeignKey("quizzes.id"))
    question_id = Column(String)  # Reference to original question
    
    # Cached question data
    name = Column(String)
    question = Column(String)
    options = Column(JSONB)
    correct_option = Column(Integer)
    explanation = Column(Text)
    
    order_index = Column(Integer)

    #Relationships
    quiz = relationship("Quiz", back_populates="questions")

class QuizSession(Base):
    __tablename__ = "quiz_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    quiz_id = Column(String, ForeignKey("quizzes.id", ondelete="RESTRICT"))
    user_id = Column(String, nullable=False)
    
    # Properties
    question_count = Column(Integer, nullable=False)
    time_limit_seconds = Column(Integer, nullable=True)

    # State
    attempt_number = Column(Integer, nullable=False)
    question_progress_index = Column(Integer, default=0, nullable=False) #old name: current_question_index
    score = Column(Integer, default=0)
    wrong_answers = Column(Integer, default=0)
    unanswered_questions = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    completion_details = Column(String, nullable=True)
    
    # Relationships
    quiz = relationship("Quiz", back_populates="sessions")
    answers = relationship("Answer", back_populates="quiz_session")

    # Computed
    @property
    def time_taken_seconds(self):
        if self.completed_at and self.started_at:
            return int((self.completed_at - self.started_at).total_seconds())
        return None
    
    @property
    def score_percentage(self):
        if self.question_count > 0:
            return (self.score / self.question_count) * 100
        return 0

class Answer(Base):
    __tablename__ = "answers"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    quiz_session_id = Column(String, ForeignKey("quiz_sessions.id"))
    quiz_question_id = Column(String, ForeignKey("quiz_questions.id"))
    
    selected_option = Column(Integer, nullable=False)
    is_correct = Column(Boolean)

    answered_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    submitted_at = Column(DateTime, onupdate=datetime.utcnow)
    revision_count = Column(Integer, default=0) # Times answer changed before quiz submission (tracker field)
    attempt_number = Column(Integer, default=1) # Times answer resubmitted (for interactive sessions - unique per attempt field)
    
    # Relationships
    quiz_session = relationship("QuizSession", back_populates="answers")
    quiz_question = relationship("QuizQuestion")

    # Can't have two answers in a session with the same attempt number
    __table_args__ = ( UniqueConstraint('quiz_session_id', 'quiz_question_id', 'attempt_number'), )