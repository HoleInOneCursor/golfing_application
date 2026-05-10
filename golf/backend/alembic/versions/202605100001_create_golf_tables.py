"""create golf tables

Revision ID: 202605100001
Revises:
Create Date: 2026-05-10 23:09:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "202605100001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "courses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("location", sa.String(length=120), nullable=False),
        sa.Column("holes", sa.Integer(), nullable=False),
        sa.Column("par", sa.Integer(), nullable=False),
        sa.CheckConstraint("holes >= 1 AND holes <= 18", name="ck_courses_holes_range"),
        sa.CheckConstraint("par >= 1", name="ck_courses_par_positive"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_courses_id"), "courses", ["id"], unique=False)
    op.create_index(op.f("ix_courses_name"), "courses", ["name"], unique=True)

    op.create_table(
        "rounds",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("player_name", sa.String(length=120), nullable=False),
        sa.Column("date_played", sa.Date(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False, server_default="0"),
        sa.CheckConstraint("score >= 0", name="ck_rounds_score_nonnegative"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_rounds_course_id"), "rounds", ["course_id"], unique=False)
    op.create_index(op.f("ix_rounds_date_played"), "rounds", ["date_played"], unique=False)
    op.create_index(op.f("ix_rounds_id"), "rounds", ["id"], unique=False)

    op.create_table(
        "hole_scores",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("round_id", sa.Integer(), nullable=False),
        sa.Column("hole_number", sa.Integer(), nullable=False),
        sa.Column("strokes", sa.Integer(), nullable=False),
        sa.CheckConstraint("hole_number >= 1", name="ck_hole_scores_hole_number_positive"),
        sa.CheckConstraint("strokes >= 1", name="ck_hole_scores_strokes_positive"),
        sa.ForeignKeyConstraint(["round_id"], ["rounds.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("round_id", "hole_number", name="uq_hole_scores_round_hole"),
    )
    op.create_index(op.f("ix_hole_scores_id"), "hole_scores", ["id"], unique=False)
    op.create_index(op.f("ix_hole_scores_round_id"), "hole_scores", ["round_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_hole_scores_round_id"), table_name="hole_scores")
    op.drop_index(op.f("ix_hole_scores_id"), table_name="hole_scores")
    op.drop_table("hole_scores")

    op.drop_index(op.f("ix_rounds_id"), table_name="rounds")
    op.drop_index(op.f("ix_rounds_date_played"), table_name="rounds")
    op.drop_index(op.f("ix_rounds_course_id"), table_name="rounds")
    op.drop_table("rounds")

    op.drop_index(op.f("ix_courses_name"), table_name="courses")
    op.drop_index(op.f("ix_courses_id"), table_name="courses")
    op.drop_table("courses")
