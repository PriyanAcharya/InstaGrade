from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[int] = None
    is_instructor: bool = False

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    is_instructor: bool = False

class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str]
    is_instructor: bool
    class Config:
        orm_mode = True

class AssignmentCreate(BaseModel):
    title: str
    description: Optional[str]
    deadline: Optional[datetime]
    language: str

class AssignmentOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    language: str
    created_at: datetime
    class Config:
        orm_mode = True

class TestCaseCreate(BaseModel):
    points: float = 1.0
    is_public: bool = True

class SubmissionOut(BaseModel):
    id: int
    assignment_id: int
    student_id: int
    score: float
    created_at: datetime
    result_json: Optional[str]
    class Config:
        orm_mode = True
