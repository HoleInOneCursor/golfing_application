from __future__ import annotations

from datetime import date as date_type

from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Course(Base):
    __tablename__ = "courses"
    __table_args__ = (
        CheckConstraint("holes >= 1 AND holes <= 18", name="ck_courses_holes_range"),
        CheckConstraint("par >= 1", name="ck_courses_par_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    location: Mapped[str] = mapped_column(String(120), nullable=False)
    holes: Mapped[int] = mapped_column(Integer, nullable=False)
    par: Mapped[int] = mapped_column(Integer, nullable=False)

    rounds: Mapped[list["Round"]] = relationship(
        back_populates="course",
        cascade="all, delete-orphan",
    )


class Round(Base):
    __tablename__ = "rounds"
    __table_args__ = (
        CheckConstraint("score >= 0", name="ck_rounds_score_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id"),
        nullable=False,
        index=True,
    )
    player_name: Mapped[str] = mapped_column(String(120), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    date_played: Mapped[date_type] = mapped_column(Date, nullable=False, index=True)

    course: Mapped[Course] = relationship(back_populates="rounds")
