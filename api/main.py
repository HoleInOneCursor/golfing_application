from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Annotated, Any, Iterator

from fastapi import FastAPI, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, model_validator


DATABASE_PATH = Path(os.getenv("GOLF_DB_PATH", "golf_scores.db"))
SCORING_MODE = "stableford"
DEFAULT_CORS_ORIGINS = "http://localhost:3000"


class HoleIn(BaseModel):
    number: int = Field(ge=1, le=18)
    par: int = Field(ge=1, le=8)
    handicap_rank: int | None = Field(default=None, ge=1, le=18)


class TeeSetIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    color: str | None = Field(default=None, max_length=40)
    total_yards: int | None = Field(default=None, ge=1, le=9000)


class CourseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    holes: list[HoleIn] = Field(min_length=1, max_length=18)
    tee_sets: list[TeeSetIn] = Field(default_factory=list, max_length=8)

    @model_validator(mode="after")
    def validate_course(self) -> "CourseCreate":
        numbers = [hole.number for hole in self.holes]
        if len(numbers) != len(set(numbers)):
            raise ValueError("hole numbers must be unique")
        if sorted(numbers) != list(range(1, len(numbers) + 1)):
            raise ValueError("hole numbers must start at 1 and be consecutive")

        ranks = [hole.handicap_rank for hole in self.holes if hole.handicap_rank is not None]
        if len(ranks) != len(set(ranks)):
            raise ValueError("handicap ranks must be unique when provided")

        tee_names = [tee.name.strip().lower() for tee in self.tee_sets]
        if len(tee_names) != len(set(tee_names)):
            raise ValueError("tee set names must be unique per course")
        return self


class PlayerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    handicap_index: float | None = Field(default=None, ge=-10, le=54)


class ScoreIn(BaseModel):
    hole_number: int = Field(ge=1, le=18)
    strokes: int = Field(ge=1, le=30)


class RoundCreate(BaseModel):
    course_id: int = Field(ge=1)
    player_id: int | None = Field(default=None, ge=1)
    player_name: str | None = Field(default=None, min_length=1, max_length=120)
    tee_set_id: int | None = Field(default=None, ge=1)
    played_on: str | None = None
    scoring_mode: str = Field(default=SCORING_MODE)
    scores: list[ScoreIn] = Field(default_factory=list, max_length=18)

    @model_validator(mode="after")
    def validate_round(self) -> "RoundCreate":
        if self.player_id is None and not (self.player_name and self.player_name.strip()):
            raise ValueError("player_id or player_name is required")
        if self.scoring_mode != SCORING_MODE:
            raise ValueError(f"scoring_mode must be {SCORING_MODE}")

        numbers = [score.hole_number for score in self.scores]
        if len(numbers) != len(set(numbers)):
            raise ValueError("score hole numbers must be unique")
        return self


class ScoreUpdate(BaseModel):
    strokes: int = Field(ge=1, le=30)


app = FastAPI(title="Golf Score Tracker API")


def configured_cors_origins() -> list[str]:
    return [
        origin.strip()
        for origin in os.getenv("CORS_ALLOW_ORIGINS", DEFAULT_CORS_ORIGINS).split(",")
        if origin.strip()
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=configured_cors_origins(),
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


def table_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {row["name"] for row in rows}


def add_column_if_missing(
    conn: sqlite3.Connection, table_name: str, column_name: str, definition: str
) -> None:
    if column_name not in table_columns(conn, table_name):
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")


def stableford_points(strokes: int | None, par: int) -> int | None:
    if strokes is None:
        return None

    score_to_par = strokes - par
    if score_to_par <= -3:
        return 5
    if score_to_par == -2:
        return 4
    if score_to_par == -1:
        return 3
    if score_to_par == 0:
        return 2
    if score_to_par == 1:
        return 1
    return 0


def parse_metadata(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def record_activity(
    conn: sqlite3.Connection,
    event_type: str,
    summary: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    conn.execute(
        """
        INSERT INTO activity_events (event_type, summary, metadata)
        VALUES (?, ?, ?)
        """,
        (event_type, summary, json.dumps(metadata or {}, sort_keys=True)),
    )


def fetch_player(conn: sqlite3.Connection, player_id: int) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT id, name, handicap_index, created_at FROM players WHERE id = ?",
        (player_id,),
    ).fetchone()
    return row_to_dict(row) if row else None


def fetch_or_create_player(
    conn: sqlite3.Connection, name: str, handicap_index: float | None = None
) -> dict[str, Any]:
    normalized_name = name.strip()
    existing = conn.execute(
        "SELECT id FROM players WHERE lower(name) = lower(?)",
        (normalized_name,),
    ).fetchone()
    if existing:
        return fetch_player(conn, existing["id"])

    cursor = conn.execute(
        "INSERT INTO players (name, handicap_index) VALUES (?, ?)",
        (normalized_name, handicap_index),
    )
    player = fetch_player(conn, cursor.lastrowid)
    record_activity(
        conn,
        "player_created",
        f"Added player {player['name']}",
        {"player_id": player["id"], "handicap_index": player["handicap_index"]},
    )
    return player


def fetch_tee_set(conn: sqlite3.Connection, tee_set_id: int) -> dict[str, Any] | None:
    row = conn.execute(
        """
        SELECT id, course_id, name, color, total_yards, created_at
        FROM tee_sets
        WHERE id = ?
        """,
        (tee_set_id,),
    ).fetchone()
    return row_to_dict(row) if row else None


def default_tee_sets() -> list[TeeSetIn]:
    return [
        TeeSetIn(name="Championship", color="Black"),
        TeeSetIn(name="Member", color="White"),
        TeeSetIn(name="Forward", color="Gold"),
    ]


def fetch_course(
    conn: sqlite3.Connection, course_id: int, include_rounds: bool = False
) -> dict[str, Any] | None:
    course = conn.execute(
        "SELECT id, name, created_at FROM courses WHERE id = ?",
        (course_id,),
    ).fetchone()
    if course is None:
        return None

    holes = conn.execute(
        """
        SELECT number, par, COALESCE(handicap_rank, number) AS handicap_rank
        FROM holes
        WHERE course_id = ?
        ORDER BY number
        """,
        (course_id,),
    ).fetchall()
    tee_sets = conn.execute(
        """
        SELECT id, course_id, name, color, total_yards, created_at
        FROM tee_sets
        WHERE course_id = ?
        ORDER BY id
        """,
        (course_id,),
    ).fetchall()

    payload = row_to_dict(course)
    payload["holes"] = [row_to_dict(hole) for hole in holes]
    payload["tee_sets"] = [row_to_dict(tee_set) for tee_set in tee_sets]
    payload["total_par"] = sum(hole["par"] for hole in holes)
    if include_rounds:
        round_rows = conn.execute(
            """
            SELECT id
            FROM rounds
            WHERE course_id = ?
            ORDER BY played_on DESC, id DESC
            """,
            (course_id,),
        ).fetchall()
        payload["rounds"] = [fetch_round(conn, row["id"]) for row in round_rows if row["id"]]
    return payload


def fetch_round(conn: sqlite3.Connection, round_id: int) -> dict[str, Any] | None:
    round_row = conn.execute(
        """
        SELECT rounds.id, rounds.course_id, rounds.player_id, rounds.tee_set_id,
               rounds.player_name, rounds.played_on, rounds.scoring_mode,
               rounds.created_at, courses.name AS course_name,
               players.name AS stored_player_name,
               players.handicap_index AS player_handicap_index,
               tee_sets.name AS tee_set_name, tee_sets.color AS tee_set_color,
               tee_sets.total_yards AS tee_set_total_yards
        FROM rounds
        JOIN courses ON courses.id = rounds.course_id
        LEFT JOIN players ON players.id = rounds.player_id
        LEFT JOIN tee_sets ON tee_sets.id = rounds.tee_set_id
        WHERE rounds.id = ?
        """,
        (round_id,),
    ).fetchone()
    if round_row is None:
        return None

    scores = conn.execute(
        """
        SELECT holes.number AS hole_number, holes.par,
               COALESCE(holes.handicap_rank, holes.number) AS handicap_rank,
               scores.strokes
        FROM holes
        LEFT JOIN scores
          ON scores.hole_number = holes.number AND scores.round_id = ?
        WHERE holes.course_id = ?
        ORDER BY holes.number
        """,
        (round_id, round_row["course_id"]),
    ).fetchall()

    score_payload = []
    for score in scores:
        score_dict = row_to_dict(score)
        score_dict["score_to_par"] = (
            score_dict["strokes"] - score_dict["par"] if score_dict["strokes"] is not None else None
        )
        score_dict["stableford_points"] = stableford_points(
            score_dict["strokes"], score_dict["par"]
        )
        score_payload.append(score_dict)

    total_strokes = sum(score["strokes"] or 0 for score in score_payload)
    completed_scores = [score for score in score_payload if score["strokes"] is not None]
    completed_holes = len(completed_scores)
    total_par = sum(score["par"] for score in score_payload)
    completed_par = sum(score["par"] for score in completed_scores)
    total_stableford_points = sum(score["stableford_points"] or 0 for score in score_payload)
    player_name = round_row["stored_player_name"] or round_row["player_name"]

    payload = row_to_dict(round_row)
    payload["player_name"] = player_name
    payload["player"] = {
        "id": round_row["player_id"],
        "name": player_name,
        "handicap_index": round_row["player_handicap_index"],
        "handicap_status": "stub",
    }
    payload["tee_set"] = (
        {
            "id": round_row["tee_set_id"],
            "name": round_row["tee_set_name"],
            "color": round_row["tee_set_color"],
            "total_yards": round_row["tee_set_total_yards"],
        }
        if round_row["tee_set_id"]
        else None
    )
    payload["scores"] = score_payload
    payload["completed_holes"] = completed_holes
    payload["total_strokes"] = total_strokes
    payload["total_par"] = total_par
    payload["score_to_par"] = total_strokes - completed_par
    payload["stableford_points"] = total_stableford_points
    payload["summary"] = {
        "scorecard": f"{total_strokes or '-'} strokes",
        "stableford": f"{total_stableford_points} pts",
        "completion": f"{completed_holes}/{len(score_payload)} holes",
        "handicap": "Handicap index is captured for demo; net strokes are not applied.",
    }
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
                handicap_rank INTEGER,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
                UNIQUE (course_id, number)
            );

            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                handicap_index REAL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS tee_sets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                color TEXT,
                total_yards INTEGER,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
                UNIQUE (course_id, name)
            );

            CREATE TABLE IF NOT EXISTS rounds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                player_id INTEGER,
                tee_set_id INTEGER,
                player_name TEXT NOT NULL,
                played_on TEXT NOT NULL,
                scoring_mode TEXT NOT NULL DEFAULT 'stableford',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
                FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE SET NULL,
                FOREIGN KEY (tee_set_id) REFERENCES tee_sets(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                round_id INTEGER NOT NULL,
                hole_number INTEGER NOT NULL,
                strokes INTEGER NOT NULL,
                FOREIGN KEY (round_id) REFERENCES rounds(id) ON DELETE CASCADE,
                UNIQUE (round_id, hole_number)
            );

            CREATE TABLE IF NOT EXISTS activity_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                summary TEXT NOT NULL,
                metadata TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        add_column_if_missing(conn, "holes", "handicap_rank", "INTEGER")
        add_column_if_missing(conn, "rounds", "player_id", "INTEGER")
        add_column_if_missing(conn, "rounds", "tee_set_id", "INTEGER")
        add_column_if_missing(conn, "rounds", "scoring_mode", "TEXT NOT NULL DEFAULT 'stableford'")

        legacy_rounds = conn.execute(
            """
            SELECT DISTINCT player_name
            FROM rounds
            WHERE player_name IS NOT NULL AND trim(player_name) != ''
            """
        ).fetchall()
        for row in legacy_rounds:
            player = fetch_or_create_player(conn, row["player_name"])
            conn.execute(
                """
                UPDATE rounds
                SET player_id = ?
                WHERE player_id IS NULL AND lower(player_name) = lower(?)
                """,
                (player["id"], row["player_name"]),
            )

        courses = conn.execute("SELECT id FROM courses").fetchall()
        for course in courses:
            tee_count = conn.execute(
                "SELECT COUNT(*) AS count FROM tee_sets WHERE course_id = ?",
                (course["id"],),
            ).fetchone()["count"]
            if tee_count == 0:
                conn.execute(
                    """
                    INSERT INTO tee_sets (course_id, name, color)
                    VALUES (?, ?, ?)
                    """,
                    (course["id"], "Member", "White"),
                )

        conn.execute(
            """
            UPDATE holes
            SET handicap_rank = number
            WHERE handicap_rank IS NULL
            """
        )
        conn.execute(
            """
            UPDATE rounds
            SET tee_set_id = (
                SELECT tee_sets.id
                FROM tee_sets
                WHERE tee_sets.course_id = rounds.course_id
                ORDER BY tee_sets.id
                LIMIT 1
            )
            WHERE tee_set_id IS NULL
            """
        )


@app.on_event("startup")
def on_startup() -> None:
    ensure_schema()


@app.get("/api/health")
@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/players")
@app.get("/players")
def list_players() -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, name, handicap_index, created_at FROM players ORDER BY name"
        ).fetchall()
        return [row_to_dict(row) for row in rows]


@app.post("/api/players", status_code=201)
@app.post("/players", status_code=201)
def create_player(player: PlayerCreate) -> dict[str, Any]:
    with get_db() as conn:
        try:
            cursor = conn.execute(
                "INSERT INTO players (name, handicap_index) VALUES (?, ?)",
                (player.name.strip(), player.handicap_index),
            )
        except sqlite3.IntegrityError as exc:
            raise HTTPException(status_code=409, detail="player name already exists") from exc

        created = fetch_player(conn, cursor.lastrowid)
        record_activity(
            conn,
            "player_created",
            f"Added player {created['name']}",
            {"player_id": created["id"], "handicap_index": created["handicap_index"]},
        )
        return created


@app.get("/api/courses")
@app.get("/courses")
def list_courses() -> list[dict[str, Any]]:
    with get_db() as conn:
        course_rows = conn.execute("SELECT id FROM courses ORDER BY name").fetchall()
        return [fetch_course(conn, row["id"]) for row in course_rows if row["id"]]


@app.post("/api/courses", status_code=201)
@app.post("/courses", status_code=201)
def create_course(course: CourseCreate) -> dict[str, Any]:
    tee_sets = course.tee_sets or default_tee_sets()

    with get_db() as conn:
        try:
            cursor = conn.execute("INSERT INTO courses (name) VALUES (?)", (course.name.strip(),))
        except sqlite3.IntegrityError as exc:
            raise HTTPException(status_code=409, detail="course name already exists") from exc

        course_id = cursor.lastrowid
        conn.executemany(
            "INSERT INTO holes (course_id, number, par, handicap_rank) VALUES (?, ?, ?, ?)",
            [
                (course_id, hole.number, hole.par, hole.handicap_rank or hole.number)
                for hole in course.holes
            ],
        )
        conn.executemany(
            """
            INSERT INTO tee_sets (course_id, name, color, total_yards)
            VALUES (?, ?, ?, ?)
            """,
            [
                (course_id, tee.name.strip(), tee.color, tee.total_yards)
                for tee in tee_sets
            ],
        )
        created = fetch_course(conn, course_id)
        record_activity(
            conn,
            "course_created",
            f"Added course {created['name']} with {len(created['tee_sets'])} tee sets",
            {"course_id": course_id, "tee_sets": [tee["name"] for tee in created["tee_sets"]]},
        )
        return created


@app.get("/api/courses/{course_id}")
@app.get("/courses/{course_id}")
def get_course(course_id: int) -> dict[str, Any]:
    with get_db() as conn:
        course = fetch_course(conn, course_id, include_rounds=True)
        if course is None:
            raise HTTPException(status_code=404, detail="course not found")
        return course


@app.delete("/api/courses/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
@app.delete("/courses/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(course_id: int) -> Response:
    with get_db() as conn:
        course = fetch_course(conn, course_id)
        if course is None:
            raise HTTPException(status_code=404, detail="course not found")

        conn.execute("DELETE FROM courses WHERE id = ?", (course_id,))
        record_activity(
            conn,
            "course_deleted",
            f"Deleted course {course['name']}",
            {"course_id": course_id},
        )
        return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/api/rounds")
@app.get("/rounds")
def list_rounds() -> list[dict[str, Any]]:
    with get_db() as conn:
        round_rows = conn.execute(
            "SELECT id FROM rounds ORDER BY played_on DESC, id DESC"
        ).fetchall()
        return [fetch_round(conn, row["id"]) for row in round_rows if row["id"]]


@app.post("/api/rounds", status_code=201)
@app.post("/rounds", status_code=201)
def create_round(round_data: RoundCreate) -> dict[str, Any]:
    played_on = round_data.played_on or date.today().isoformat()

    with get_db() as conn:
        course = fetch_course(conn, round_data.course_id)
        if course is None:
            raise HTTPException(status_code=404, detail="course not found")

        if round_data.player_id:
            player = fetch_player(conn, round_data.player_id)
            if player is None:
                raise HTTPException(status_code=404, detail="player not found")
        else:
            player = fetch_or_create_player(conn, round_data.player_name)

        if round_data.tee_set_id:
            tee_set = fetch_tee_set(conn, round_data.tee_set_id)
            if tee_set is None or tee_set["course_id"] != round_data.course_id:
                raise HTTPException(status_code=400, detail="tee set is not on this course")
        else:
            tee_set = course["tee_sets"][0] if course["tee_sets"] else None

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
            """
            INSERT INTO rounds (course_id, player_id, tee_set_id, player_name, played_on, scoring_mode)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                round_data.course_id,
                player["id"],
                tee_set["id"] if tee_set else None,
                player["name"],
                played_on,
                SCORING_MODE,
            ),
        )
        round_id = cursor.lastrowid
        conn.executemany(
            "INSERT INTO scores (round_id, hole_number, strokes) VALUES (?, ?, ?)",
            [(round_id, score.hole_number, score.strokes) for score in round_data.scores],
        )
        created = fetch_round(conn, round_id)
        record_activity(
            conn,
            "round_created",
            f"Started Stableford round for {created['player_name']} at {created['course_name']}",
            {
                "round_id": round_id,
                "course_id": round_data.course_id,
                "player_id": player["id"],
                "tee_set_id": tee_set["id"] if tee_set else None,
            },
        )
        return created


@app.get("/api/rounds/{round_id}")
@app.get("/rounds/{round_id}")
def get_round(round_id: int) -> dict[str, Any]:
    with get_db() as conn:
        round_payload = fetch_round(conn, round_id)
        if round_payload is None:
            raise HTTPException(status_code=404, detail="round not found")
        return round_payload


@app.delete("/api/rounds/{round_id}", status_code=status.HTTP_204_NO_CONTENT)
@app.delete("/rounds/{round_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_round(round_id: int) -> Response:
    with get_db() as conn:
        round_payload = fetch_round(conn, round_id)
        if round_payload is None:
            raise HTTPException(status_code=404, detail="round not found")

        conn.execute("DELETE FROM rounds WHERE id = ?", (round_id,))
        record_activity(
            conn,
            "round_deleted",
            f"Deleted round for {round_payload['player_name']} at {round_payload['course_name']}",
            {"round_id": round_id, "course_id": round_payload["course_id"]},
        )
        return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/api/stats/leaderboard")
@app.get("/stats/leaderboard")
def leaderboard() -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute(
            """
            WITH round_totals AS (
                SELECT
                    rounds.id AS round_id,
                    rounds.player_id,
                    COALESCE(players.name, rounds.player_name) AS player_name,
                    SUM(scores.strokes) AS total_strokes,
                    COUNT(scores.id) AS holes_scored
                FROM rounds
                JOIN scores ON scores.round_id = rounds.id
                LEFT JOIN players ON players.id = rounds.player_id
                GROUP BY rounds.id
                HAVING COUNT(scores.id) > 0
            )
            SELECT
                player_id,
                player_name,
                COUNT(round_id) AS rounds_played,
                ROUND(AVG(total_strokes), 2) AS average_score,
                MIN(total_strokes) AS best_score,
                MAX(total_strokes) AS worst_score,
                SUM(holes_scored) AS holes_scored
            FROM round_totals
            GROUP BY player_id, lower(player_name), player_name
            ORDER BY average_score ASC, rounds_played DESC, lower(player_name) ASC
            """
        ).fetchall()

    leaders: list[dict[str, Any]] = []
    previous_average: float | None = None
    previous_rank = 0
    for index, row in enumerate(rows, start=1):
        item = row_to_dict(row)
        average_score = float(item["average_score"])
        rank = previous_rank if previous_average == average_score else index
        item["rank"] = rank
        item["average_score"] = average_score
        leaders.append(item)
        previous_average = average_score
        previous_rank = rank
    return leaders


@app.put("/api/rounds/{round_id}/scores/{hole_number}")
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
        updated = fetch_round(conn, round_id)
        score_row = next(
            hole for hole in updated["scores"] if hole["hole_number"] == hole_number
        )
        record_activity(
            conn,
            "score_updated",
            (
                f"{updated['player_name']} posted {score.strokes} on hole {hole_number} "
                f"for {score_row['stableford_points']} Stableford pts"
            ),
            {
                "round_id": round_id,
                "hole_number": hole_number,
                "strokes": score.strokes,
                "stableford_points": score_row["stableford_points"],
            },
        )
        return updated


@app.get("/api/activity")
@app.get("/activity")
def list_activity(limit: Annotated[int, Query(ge=1, le=100)] = 20) -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT id, event_type, summary, metadata, created_at
            FROM activity_events
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        activity = []
        for row in rows:
            item = row_to_dict(row)
            item["metadata"] = parse_metadata(item["metadata"])
            activity.append(item)
        return activity


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host="0.0.0.0", port=8787, reload=True)
