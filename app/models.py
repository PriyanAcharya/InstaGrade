from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_instructor = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    assignments = relationship("Assignment", back_populates="creator")
    submissions = relationship("Submission", back_populates="student")

class Assignment(Base):
    __tablename__ = "assignments"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    deadline = Column(DateTime(timezone=True))
    language = Column(String, nullable=False)
    creator_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    creator = relationship("User", back_populates="assignments")
    testcases = relationship("TestCase", back_populates="assignment")
    submissions = relationship("Submission", back_populates="assignment")

class TestCase(Base):
    __tablename__ = "testcases"
    id = Column(Integer, primary_key=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"))
    input_path = Column(String, nullable=False)
    expected_output_path = Column(String, nullable=False)
    points = Column(Float, default=1.0)
    is_public = Column(Boolean, default=True)

    assignment = relationship("Assignment", back_populates="testcases")

class Submission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"))
    student_id = Column(Integer, ForeignKey("users.id"))
    file_path = Column(String, nullable=False)
    language = Column(String, nullable=False)
    score = Column(Float, default=0.0)
    result_json = Column(Text) # JSON string of per-test-case results
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    exec_time = Column(Float, nullable=True)

    assignment = relationship("Assignment", back_populates="submissions")
    student = relationship("User", back_populates="submissions")
