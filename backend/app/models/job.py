from datetime import date

from pgvector.sqlalchemy import Vector
from sqlalchemy import Date, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

EMBEDDING_DIMENSIONS = 1536


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    remote: Mapped[str] = mapped_column(String(32), nullable=False)
    experience_min_years: Mapped[int] = mapped_column(Integer, nullable=False)
    experience_max_years: Mapped[int] = mapped_column(Integer, nullable=False)
    salary_range_inr_lpa: Mapped[str | None] = mapped_column(String(64), nullable=True)
    salary_range_usd: Mapped[str | None] = mapped_column(String(64), nullable=True)
    posted_date: Mapped[date] = mapped_column(Date, nullable=False)
    skills_required: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    apply_url: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIMENSIONS), nullable=True)

    def embedding_text(self) -> str:
        skills = ", ".join(self.skills_required)
        return f"{self.title} at {self.company}\nSkills: {skills}\n{self.description}"
