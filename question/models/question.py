from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import uuid

Base = declarative_base()

class Topic(Base):
    """
    Topic model - represents a question category.
    One-to-many relationship: One Topic has many Questions.
    """
    __tablename__ = "topics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=True)

    # Relationship: One Topic has many Questions
    # back_populates creates bidirectional relationship
    questions = relationship("Question", back_populates="topic")

class Question(Base):
    """
    Question model - now references Topic via foreign key.
    Many-to-one relationship: Many Questions belong to one Topic.
    """
    __tablename__ = "questions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    topic_id = Column(String, ForeignKey("topics.id"), nullable=False)  # Foreign key to topics table
    name = Column(String, nullable=False)
    question = Column(Text, nullable=False)
    options = Column(JSONB, nullable=False)
    correct_option = Column(Integer, nullable=False)
    explanation = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)

    # Relationship: Many Questions belong to one Topic
    topic = relationship("Topic", back_populates="questions")
