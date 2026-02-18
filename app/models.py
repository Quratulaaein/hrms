from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(String, primary_key=True)
    name = Column(String)
    email = Column(String)
    phone = Column(String)
    role = Column(String)
    username = Column(String(100), unique=True)
    password = Column(String(100))


    password = Column(String)  # candidate login password
    interview_link = Column(String)

    cv_score = Column(Integer)
    status = Column(String)

    interview_completed = Column(Boolean, default=False)

    overall_score = Column(Float)
    decision = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)


class InterviewAnswer(Base):
    __tablename__ = "interview_answers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(String)
    question_number = Column(Integer)
    question_text = Column(Text)

    audio_path = Column(String)

    manual_score = Column(Integer)  # HR manual rating

    created_at = Column(DateTime, default=datetime.utcnow)
