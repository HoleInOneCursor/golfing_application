from __future__ import annotations

from datetime import date as date_type

from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, String, UniqueConstraint
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
        passive_deletes=True,
    )


class Round(Base):
    __tablename__ = "rounds"
    __table_args__ = (
        CheckConstraint("total_score >= 0", name="ck_rounds_total_score_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    player_name: Mapped[str] = mapped_column(String(120), nullable=False)
    date: Mapped[date_type] = mapped_column(Date, nullable=False, index=True)
    total_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    course: Mapped[Course] = relationship(back_populates="rounds")
    hole_scores: Mapped[list["HoleScore"]] = relationship(
        back_populates="round",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="HoleScore.hole_number",
    )


class HoleScore(Base):
    __tablename__ = "hole_scores"
    __table_args__ = (
        UniqueConstraint("round_id", "hole_number", name="uq_hole_scores_round_hole"),
        CheckConstraint("hole_number >= 1", name="ck_hole_scores_hole_number_positive"),
        CheckConstraint("strokes >= 1", name="ck_hole_scores_strokes_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    round_id: Mapped[int] = mapped_column(
        ForeignKey("rounds.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    hole_number: Mapped[int] = mapped_column(Integer, nullable=False)
    strokes: Mapped[int] = mapped_column(Integer, nullable=False)

    round: Mapped[Round] = relationship(back_populates="hole_scores")
