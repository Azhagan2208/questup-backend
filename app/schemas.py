from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime


class TeacherRequestCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class TeacherOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True


class TeacherRegister(BaseModel):
    name: str
    email: EmailStr
    password: str


class TeacherLogin(BaseModel):
    email: EmailStr
    password: str


class SubjectCreate(BaseModel):
    name: str


class SubjectOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class RoomCreate(BaseModel):
    title: str
    subject_id: Optional[int] = None


class RoomOut(BaseModel):
    id: int
    title: str
    room_code: str
    subject_id: Optional[int]
    owner_id: int
    is_open: bool
    created_at: datetime

    class Config:
        from_attributes = True


class QuestionCreate(BaseModel):
    title: str
    description: Optional[str] = None
    student_name: Optional[str] = None


class QuestionOut(BaseModel):
    id: int
    room_id: int
    title: str
    description: Optional[str]
    student_name: Optional[str]
    created_at: datetime
    is_solved: bool
    votes: int = 0

    class Config:
        from_attributes = True


class AnswerCreate(BaseModel):
    content: str


class AnswerOut(BaseModel):
    id: int
    question_id: int
    teacher_id: int
    content: str
    created_at: datetime
    is_accepted: bool

    class Config:
        from_attributes = True


class VoteCreate(BaseModel):
    vote_type: str
    voter_token: Optional[str] = None


class ApproveRequest(BaseModel):
    password: Optional[str] = "password123"

    @field_validator("password", mode="before")
    @classmethod
    def truncate_password(cls, v):
        if v:
            v_bytes = v.encode("utf-8")
            if len(v_bytes) > 72:
                v_bytes = v_bytes[:72]
                v = v_bytes.decode("utf-8", errors="ignore")
        return v or "password123"
