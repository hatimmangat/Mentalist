from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
import datetime


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    display_name: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: str
    display_name: Optional[str]

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    session_id: Optional[int] = None
    message: str


class SourceOut(BaseModel):
    doc_title: str
    section_title: str
    similarity: float


class ChatResponse(BaseModel):
    session_id: int
    reply: str
    sources: List[SourceOut]
    crisis_detected: bool


class SessionOut(BaseModel):
    id: int
    started_at: datetime.datetime
    ended_at: Optional[datetime.datetime]

    class Config:
        from_attributes = True


class ReportResponse(BaseModel):
    session_id: int
    report: str
    generated_at: datetime.datetime
    message_count: int
