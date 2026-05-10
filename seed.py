from __future__ import annotations

from typing import Any

from api.main import (
    DATABASE_PATH,
    SCORING_MODE,
    ensure_schema,
    fetch_course,
    fetch_or_create_player,
    get_db,
    record_activity,
)


def create_course_if_missing(
    conn,
    name: str,
    pars: list[int],
    handicap_ranks: list[int],
    tee_sets: list[dict[str, Any]],
) -> dict[str, Any]:
    existing = conn.execute("SELECT id FROM courses WHERE lower(name) = lower(?)", (name,)).fetchone()
    if existing:
        return fetch_course(conn, existing["id"])

    cursor = conn.execute("INSERT INTO courses (name) VALUES (?)", (name,))
    course_id = cursor.lastrowid
    conn.executemany(
        "INSERT INTO holes (course_id, number, par, handicap_rank) VALUES (?, ?, ?, ?)",
        [
            (course_id, index + 1, par, handicap_ranks[index])
            for index, par in enumerate(pars)
        ],
    )
    conn.executemany(
        """
        INSERT INTO tee_sets (course_id, name, color, total_yards)
        VALUES (?, ?, ?, ?)
        """,
        [
            (course_id, tee_set["name"], tee_set.get("color"), tee_set.get("total_yards"))
            for tee_set in tee_sets
        ],
    )
    course = fetch_course(conn, course_id)
    record_activity(
        conn,
        "course_created",
        f"Seeded course {course['name']}",
        {"course_id": course_id, "source": "seed"},
    )
    return course


def create_round_if_missing(
    conn,
    course: dict[str, Any],
    player: dict[str, Any],
    played_on: str,
    strokes: list[int],
) -> dict[str, Any] | None:
    existing = conn.execute(
        """
        SELECT id
        FROM rounds
        WHERE course_id = ? AND player_id = ? AND played_on = ?
        """,
        (course["id"], player["id"], played_on),
    ).fetchone()
    if existing:
        return None

    tee_set = course["tee_sets"][0] if course["tee_sets"] else None
    cursor = conn.execute(
        """
        INSERT INTO rounds (course_id, player_id, tee_set_id, player_name, played_on, scoring_mode)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            course["id"],
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
        [(round_id, index + 1, score) for index, score in enumerate(strokes)],
    )
    record_activity(
        conn,
        "round_created",
        f"Seeded Stableford round for {player['name']} at {course['name']}",
        {"round_id": round_id, "course_id": course["id"], "player_id": player["id"], "source": "seed"},
    )
    return {"id": round_id, "course_id": course["id"], "player_id": player["id"]}


def main() -> None:
    ensure_schema()
    with get_db() as conn:
        emerald = create_course_if_missing(
            conn,
            "Emerald Hills Front 9",
            [4, 4, 3, 5, 4, 4, 3, 5, 4],
            [3, 7, 9, 1, 5, 4, 8, 2, 6],
            [
                {"name": "Championship", "color": "Black", "total_yards": 3475},
                {"name": "Member", "color": "White", "total_yards": 3150},
                {"name": "Forward", "color": "Gold", "total_yards": 2680},
            ],
        )
        river = create_course_if_missing(
            conn,
            "River Bend Executive",
            [3, 4, 3, 4, 3, 4],
            [5, 1, 6, 2, 4, 3],
            [
                {"name": "Member", "color": "White", "total_yards": 2180},
                {"name": "Forward", "color": "Gold", "total_yards": 1840},
            ],
        )

        players = {
            "Sam Snead": fetch_or_create_player(conn, "Sam Snead", 7.1),
            "Annika Sorenstam": fetch_or_create_player(conn, "Annika Sorenstam", 1.4),
            "Lee Elder": fetch_or_create_player(conn, "Lee Elder", 11.8),
        }

        created_rounds = [
            create_round_if_missing(conn, emerald, players["Sam Snead"], "2026-05-01", [4, 5, 3, 5, 4, 4, 3, 6, 4]),
            create_round_if_missing(conn, emerald, players["Annika Sorenstam"], "2026-05-02", [3, 4, 3, 4, 4, 3, 3, 5, 4]),
            create_round_if_missing(conn, river, players["Lee Elder"], "2026-05-03", [3, 5, 3, 4, 4, 4]),
        ]

    new_round_count = sum(1 for seeded_round in created_rounds if seeded_round)
    print(f"Seeded sample golf data in {DATABASE_PATH} ({new_round_count} new rounds).")


if __name__ == "__main__":
    main()
