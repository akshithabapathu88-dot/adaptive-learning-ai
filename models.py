from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from datetime import datetime

Base = declarative_base()

class Student(Base):
    __tablename__ = 'students'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    current_stage = Column(Integer, default=0)
    
class StudentPerformance(Base):
    __tablename__ = 'student_performance'
    
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, nullable=False)
    topic = Column(String(100), nullable=False)
    score = Column(Float, nullable=False)
    stage = Column(Integer, nullable=False)
    attempts = Column(Integer, default=1)
    difficulty_level = Column(String(20), nullable=False)
    weak_topics = Column(Text)  # JSON string of weak topics
    created_at = Column(DateTime, default=datetime.utcnow)
    
class QuizResult(Base):
    __tablename__ = 'quiz_results'
    
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, nullable=False)
    topic = Column(String(100), nullable=False)
    questions = Column(Text, nullable=False)  # JSON string of questions
    answers = Column(Text, nullable=False)    # JSON string of student answers
    correct_answers = Column(Text, nullable=False)  # JSON string of correct answers
    score = Column(Float, nullable=False)
    time_taken = Column(Integer)  # in seconds
    created_at = Column(DateTime, default=datetime.utcnow)
    
class LearningContent(Base):
    __tablename__ = 'learning_content'
    
    id = Column(Integer, primary_key=True)
    topic = Column(String(100), nullable=False)
    difficulty_level = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    key_concepts = Column(Text)  # JSON string of key concepts
    created_at = Column(DateTime, default=datetime.utcnow)
    
class Assignment(Base):
    __tablename__ = 'assignments'
    
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, nullable=False)
    topic = Column(String(100), nullable=False)
    difficulty_level = Column(String(20), nullable=False)
    assignment_text = Column(Text, nullable=False)
    completed = Column(Boolean, default=False)
    score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

# Database connection
DATABASE_URL = "sqlite:///./adaptive_learning.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    Base.metadata.create_all(bind=engine)
