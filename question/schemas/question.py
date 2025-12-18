from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
import uuid

class AnswerOption(BaseModel):
    num: int
    text: str

class QuestionBase(BaseModel):
    topic_id: str  # Changed from topic (string) to topic_id (foreign key)
    name: str
    question: str
    options: List[AnswerOption]
    correct_option: int
    explanation: str

class QuestionCreate(QuestionBase):
    pass

class Question(QuestionBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# NEW: Topic schemas
class TopicBase(BaseModel):
    name: str
    description: Optional[str] = None

class TopicCreate(TopicBase):
    """Schema for creating a new topic"""
    pass

class TopicRead(TopicBase):
    """Schema for Topic responses"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    model_config = ConfigDict(from_attributes=True)

# NEW: Query filters
class QuestionFilters(BaseModel):
    """Query parameters for filtering questions"""
    topic_id: Optional[str] = None
    limit: int = Field(10, ge=1, le=100)
    randomize: bool = False
