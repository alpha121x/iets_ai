from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=150)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    full_name: str
    country: str | None = None
    target_country: str | None = None
    target_program: str | None = None
    academic_degree: str | None = None
    graduation_year: int | None = None
    cgpa: float | None = None


class ProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    country: str | None = None
    target_country: str | None = None
    target_program: str | None = None
    academic_degree: str | None = None
    graduation_year: int | None = Field(default=None, ge=1950, le=2100)
    cgpa: float | None = Field(default=None, ge=0, le=4)


class IELTSResultCreate(BaseModel):
    reading: float = Field(ge=0, le=9)
    listening: float = Field(ge=0, le=9)
    writing: float = Field(ge=0, le=9)
    speaking: float = Field(ge=0, le=9)
    test_type: str = "Academic"
    source: str = "Manual"


class IELTSResultOut(IELTSResultCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    overall: float
    created_at: datetime


class WritingCreate(BaseModel):
    task_type: str = Field(pattern="^Task [12]$")
    question: str | None = None
    answer: str = Field(min_length=30)


class WritingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    estimated_band: float | None
    feedback: str | None
    created_at: datetime


class AttemptCreate(BaseModel):
    module: str = Field(pattern="^(Reading|Listening|Speaking)$")
    correct_answers: int = Field(ge=0)
    total_questions: int = Field(gt=0)


class LessonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    module: str
    title: str
    content: str
    level: str
