from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class University(Base):
    __tablename__ = "universities"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ranking: Mapped[int | None] = mapped_column(Integer, nullable=True)


class UniversityProgram(Base):
    __tablename__ = "university_programs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    university_id: Mapped[int] = mapped_column(
        ForeignKey("universities.id"), nullable=False, index=True
    )
    program_name: Mapped[str] = mapped_column(String(255), nullable=False)
    degree: Mapped[str | None] = mapped_column(String(100), nullable=True)
    field: Mapped[str | None] = mapped_column(String(150), nullable=True)
    min_ielts: Mapped[float | None] = mapped_column(Float, nullable=True)
    min_reading: Mapped[float | None] = mapped_column(Float, nullable=True)
    min_listening: Mapped[float | None] = mapped_column(Float, nullable=True)
    min_writing: Mapped[float | None] = mapped_column(Float, nullable=True)
    min_speaking: Mapped[float | None] = mapped_column(Float, nullable=True)
    min_cgpa: Mapped[float | None] = mapped_column(Float, nullable=True)
    tuition_fee: Mapped[float | None] = mapped_column(Float, nullable=True)
    application_deadline: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ProgramTestRequirement(Base):
    __tablename__ = "program_test_requirements"

    id: Mapped[int] = mapped_column(primary_key=True)
    program_id: Mapped[int] = mapped_column(ForeignKey("university_programs.id"), nullable=False, index=True)
    test_name: Mapped[str] = mapped_column(String(100), nullable=False)
    minimum_score: Mapped[str | None] = mapped_column(String(100), nullable=True)
    required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Scholarship(Base):
    __tablename__ = "scholarships"

    id: Mapped[int] = mapped_column(primary_key=True)
    university_id: Mapped[int | None] = mapped_column(ForeignKey("universities.id"), nullable=True, index=True)
    program_id: Mapped[int | None] = mapped_column(ForeignKey("university_programs.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[str | None] = mapped_column(String(150), nullable=True)
    eligibility: Mapped[str | None] = mapped_column(Text, nullable=True)
    deadline: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_url: Mapped[str] = mapped_column(String(500), nullable=False)
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
