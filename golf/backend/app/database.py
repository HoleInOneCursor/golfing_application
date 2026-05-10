from __future__ import annotations

import os
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


BACKEND_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE_URL = f"sqlite:///{BACKEND_DIR / 'golf.db'}"
DATABASE_URL = os.getenv("GOLF_DATABASE_URL", DEFAULT_DATABASE_URL)


class Base(DeclarativeBase):
    pass


connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record) -> None:  # noqa: ANN001
    if DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def migrate_legacy_sqlite_schema() -> None:
    if not DATABASE_URL.startswith("sqlite"):
        return

    with engine.begin() as connection:
        inspector = inspect(connection)
        table_names = set(inspector.get_table_names())

        if "rounds" in table_names:
            round_columns = {
                column["name"] for column in inspector.get_columns("rounds")
            }
            if "date" in round_columns and "date_played" not in round_columns:
                connection.execute(
                    text('ALTER TABLE rounds RENAME COLUMN "date" TO date_played')
                )
                round_columns.remove("date")
                round_columns.add("date_played")
            if "total_score" in round_columns and "score" not in round_columns:
                connection.execute(
                    text("ALTER TABLE rounds RENAME COLUMN total_score TO score")
                )
                round_columns.remove("total_score")
                round_columns.add("score")

            if "date_played" in round_columns:
                indexes = {
                    index["name"]
                    for index in inspect(connection).get_indexes("rounds")
                    if index.get("name")
                }
                if "ix_rounds_date" in indexes:
                    connection.execute(text("DROP INDEX IF EXISTS ix_rounds_date"))
                connection.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS ix_rounds_date_played "
                        "ON rounds (date_played)"
                    )
                )

        if "courses" in table_names:
            course_indexes = inspect(connection).get_indexes("courses")
            has_unique_name_index = any(
                index.get("unique") and index.get("column_names") == ["name"]
                for index in course_indexes
            )
            duplicate_course_name = connection.scalar(
                text(
                    "SELECT name FROM courses "
                    "GROUP BY name HAVING COUNT(*) > 1 LIMIT 1"
                )
            )
            if not has_unique_name_index and duplicate_course_name is None:
                connection.execute(text("DROP INDEX IF EXISTS ix_courses_name"))
                connection.execute(
                    text("CREATE UNIQUE INDEX ix_courses_name ON courses (name)")
                )


migrate_legacy_sqlite_schema()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
