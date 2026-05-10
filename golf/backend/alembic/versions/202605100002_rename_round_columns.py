"""rename round date and score columns

Revision ID: 202605100002
Revises: 202605100001
Create Date: 2026-05-10 23:35:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "202605100002"
down_revision: Union[str, None] = "202605100001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_names(table_name: str) -> set[str]:
    return {
        column["name"]
        for column in sa.inspect(op.get_bind()).get_columns(table_name)
    }


def _index_by_name(table_name: str) -> dict[str, dict[str, object]]:
    return {
        index["name"]: index
        for index in sa.inspect(op.get_bind()).get_indexes(table_name)
        if index.get("name")
    }


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    table_names = set(inspector.get_table_names())

    if "rounds" in table_names:
        round_columns = _column_names("rounds")
        if "date" in round_columns and "date_played" not in round_columns:
            op.execute('ALTER TABLE rounds RENAME COLUMN "date" TO date_played')
        if "total_score" in round_columns and "score" not in round_columns:
            op.execute("ALTER TABLE rounds RENAME COLUMN total_score TO score")

        indexes = _index_by_name("rounds")
        if "ix_rounds_date" in indexes:
            op.drop_index("ix_rounds_date", table_name="rounds")
        if "ix_rounds_date_played" not in indexes:
            op.create_index(
                op.f("ix_rounds_date_played"),
                "rounds",
                ["date_played"],
                unique=False,
            )

    if "courses" in table_names:
        indexes = _index_by_name("courses")
        has_unique_name_index = any(
            index.get("unique") and index.get("column_names") == ["name"]
            for index in indexes.values()
        )
        if not has_unique_name_index:
            if "ix_courses_name" in indexes:
                op.drop_index("ix_courses_name", table_name="courses")
            op.create_index(op.f("ix_courses_name"), "courses", ["name"], unique=True)


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    table_names = set(inspector.get_table_names())

    if "rounds" not in table_names:
        return

    indexes = _index_by_name("rounds")
    if "ix_rounds_date_played" in indexes:
        op.drop_index("ix_rounds_date_played", table_name="rounds")

    round_columns = _column_names("rounds")
    if "date_played" in round_columns and "date" not in round_columns:
        op.execute("ALTER TABLE rounds RENAME COLUMN date_played TO date")
    if "score" in round_columns and "total_score" not in round_columns:
        op.execute("ALTER TABLE rounds RENAME COLUMN score TO total_score")

    indexes = _index_by_name("rounds")
    if "ix_rounds_date" not in indexes:
        op.create_index(op.f("ix_rounds_date"), "rounds", ["date"], unique=False)
