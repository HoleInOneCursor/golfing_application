from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Any, Iterator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, model_validator


DATABASE_PATH = Path(os.getenv("GOLF_DB_PATH", "golf_scores.db"))


class HoleIn(BaseModel):
    number: int = Field(ge=1, le=18)
    par: int = Field(ge=1, le=8)


class CourseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    holes: list[HoleIn] = Field(min_length=1, max_length=18)

    @model_validator(mode="after")
    def validate_holes(self) -> "CourseCreate":
        numbers = [hole.number for hole in self.holes]
        if len(numbers) != len(set(numbers)):
            raise ValueError("hole numbers must be unique")
        if sorted(numbers) != list(range(1, len(numbers) + 1)):
            raise ValueError("hole numbers must start at 1 and be consecutive")
        return self


class ScoreIn(BaseModel):
    hole_number: int = Field(ge=1, le=18)
    strokes: int = Field(ge=1, le=30)


class RoundCreate(BaseModel):
    course_id: int = Field(ge=1)
    player_name: str = Field(min_length=1, max_length=120)
    played_on: str | None = None
    scores: list[ScoreIn] = Field(default_factory=list, max_length=18)

    @model_validator(mode="after")
    def validate_scores(self) -> "RoundCreate":
        numbers = [score.hole_number for score in self.scores]
        if len(numbers) != len(set(numbers)):
            raise ValueError("score hole numbers must be unique")
        return self


class ScoreUpdate(BaseModel):
    strokes: int = Field(ge=1, le=30)


app = FastAPI(title="Golf Score Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOW_ORIGINS", "*").split(","),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@contextmanager
def get_db() -> Iterator[sqlite3.Connection]:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {key: row[key] for key in row.keys()}


def fetch_course(conn: sqlite3.Connection, course_id: int) -> dict[str, Any] | None:
    course = conn.execute(
        "SELECT id, name, created_at FROM courses WHERE id = ?",
        (course_id,),
    ).fetchone()
    if course is None:
        return None

    holes = conn.execute(
        "SELECT number, par FROM holes WHERE course_id = ? ORDER BY number",
        (course_id,),
    ).fetchall()
    payload = row_to_dict(course)
    payload["holes"] = [row_to_dict(hole) for hole in holes]
    payload["total_par"] = sum(hole["par"] for hole in holes)
    return payload


def fetch_round(conn: sqlite3.Connection, round_id: int) -> dict[str, Any] | None:
    round_row = conn.execute(
        """
        SELECT rounds.id, rounds.course_id, rounds.player_name, rounds.played_on,
               rounds.created_at, courses.name AS course_name
        FROM rounds
        JOIN courses ON courses.id = rounds.course_id
        WHERE rounds.id = ?
        """,
        (round_id,),
    ).fetchone()
    if round_row is None:
        return None

    scores = conn.execute(
        """
        SELECT holes.number AS hole_number, holes.par, scores.strokes
        FROM holes
        LEFT JOIN scores
          ON scores.hole_number = holes.number AND scores.round_id = ?
        WHERE holes.course_id = ?
        ORDER BY holes.number
        """,
        (round_id, round_row["course_id"]),
    ).fetchall()

    score_payload = [row_to_dict(score) for score in scores]
    total_strokes = sum(score["strokes"] or 0 for score in score_payload)
    completed_holes = sum(1 for score in score_payload if score["strokes"] is not None)
    total_par = sum(score["par"] for score in score_payload)

    payload = row_to_dict(round_row)
    payload["scores"] = score_payload
    payload["completed_holes"] = completed_holes
    payload["total_strokes"] = total_strokes
    payload["total_par"] = total_par
    payload["score_to_par"] = total_strokes - sum(
        score["par"] for score in score_payload if score["strokes"] is not None
    )
    return payload


def ensure_schema() -> None:
    with get_db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS holes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                number INTEGER NOT NULL,
                par INTEGER NOT NULL,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
                UNIQUE (course_id, number)
            );

            CREATE TABLE IF NOT EXISTS rounds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                player_name TEXT NOT NULL,
                played_on TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                round_id INTEGER NOT NULL,
                hole_number INTEGER NOT NULL,
                strokes INTEGER NOT NULL,
                FOREIGN KEY (round_id) REFERENCES rounds(id) ON DELETE CASCADE,
                UNIQUE (round_id, hole_number)
            );
            """
        )


@app.on_event("startup")
def on_startup() -> None:
    ensure_schema()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/courses")
def list_courses() -> list[dict[str, Any]]:
    with get_db() as conn:
        course_rows = conn.execute("SELECT id FROM courses ORDER BY name").fetchall()
        return [fetch_course(conn, row["id"]) for row in course_rows if row["id"]]


@app.post("/courses", status_code=201)
def create_course(course: CourseCreate) -> dict[str, Any]:
    with get_db() as conn:
        try:
            cursor = conn.execute("INSERT INTO courses (name) VALUES (?)", (course.name.strip(),))
        except sqlite3.IntegrityError as exc:
            raise HTTPException(status_code=409, detail="course name already exists") from exc

        course_id = cursor.lastrowid
        conn.executemany(
            "INSERT INTO holes (course_id, number, par) VALUES (?, ?, ?)",
            [(course_id, hole.number, hole.par) for hole in course.holes],
        )
        return fetch_course(conn, course_id)


@app.get("/courses/{course_id}")
def get_course(course_id: int) -> dict[str, Any]:
    with get_db() as conn:
        course = fetch_course(conn, course_id)
        if course is None:
            raise HTTPException(status_code=404, detail="course not found")
        return course


@app.get("/rounds")
def list_rounds() -> list[dict[str, Any]]:
    with get_db() as conn:
        round_rows = conn.execute(
            "SELECT id FROM rounds ORDER BY played_on DESC, id DESC"
        ).fetchall()
        return [fetch_round(conn, row["id"]) for row in round_rows if row["id"]]


@app.post("/rounds", status_code=201)
def create_round(round_data: RoundCreate) -> dict[str, Any]:
    played_on = round_data.played_on or date.today().isoformat()

    with get_db() as conn:
        course = fetch_course(conn, round_data.course_id)
        if course is None:
            raise HTTPException(status_code=404, detail="course not found")

        valid_holes = {hole["number"] for hole in course["holes"]}
        invalid_scores = [
            score.hole_number for score in round_data.scores if score.hole_number not in valid_holes
        ]
        if invalid_scores:
            raise HTTPException(
                status_code=400,
                detail=f"scores include holes not on course: {invalid_scores}",
            )

        cursor = conn.execute(
            "INSERT INTO rounds (course_id, player_name, played_on) VALUES (?, ?, ?)",
            (round_data.course_id, round_data.player_name.strip(), played_on),
        )
        round_id = cursor.lastrowid
        conn.executemany(
            "INSERT INTO scores (round_id, hole_number, strokes) VALUES (?, ?, ?)",
            [(round_id, score.hole_number, score.strokes) for score in round_data.scores],
        )
        return fetch_round(conn, round_id)


@app.get("/rounds/{round_id}")
def get_round(round_id: int) -> dict[str, Any]:
    with get_db() as conn:
        round_payload = fetch_round(conn, round_id)
        if round_payload is None:
            raise HTTPException(status_code=404, detail="round not found")
        return round_payload


@app.put("/rounds/{round_id}/scores/{hole_number}")
def upsert_score(round_id: int, hole_number: int, score: ScoreUpdate) -> dict[str, Any]:
    with get_db() as conn:
        round_payload = fetch_round(conn, round_id)
        if round_payload is None:
            raise HTTPException(status_code=404, detail="round not found")

        valid_holes = {hole["hole_number"] for hole in round_payload["scores"]}
        if hole_number not in valid_holes:
            raise HTTPException(status_code=400, detail="hole is not on this course")

        conn.execute(
            """
            INSERT INTO scores (round_id, hole_number, strokes)
            VALUES (?, ?, ?)
            ON CONFLICT(round_id, hole_number)
            DO UPDATE SET strokes = excluded.strokes
            """,
            (round_id, hole_number, score.strokes),
        )
        return fetch_round(conn, round_id)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host="0.0.0.0", port=8787, reload=True)
