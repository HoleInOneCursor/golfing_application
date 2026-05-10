from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api import main


@pytest.fixture()
def client(tmp_path):
    main.DATABASE_PATH = tmp_path / "test_golf_scores.db"
    with TestClient(main.app) as test_client:
        yield test_client


def course_payload(name: str = "Test Links") -> dict:
    return {
        "name": name,
        "holes": [
            {"number": 1, "par": 4, "handicap_rank": 1},
            {"number": 2, "par": 4, "handicap_rank": 2},
        ],
        "tee_sets": [{"name": "Member", "color": "White", "total_yards": 720}],
    }


def create_course(client: TestClient, name: str = "Test Links") -> dict:
    response = client.post("/api/courses", json=course_payload(name))
    assert response.status_code == 201, response.text
    return response.json()


def create_round(
    client: TestClient,
    course: dict,
    player_name: str,
    strokes: list[int],
    played_on: str = "2026-05-10",
) -> dict:
    response = client.post(
        "/api/rounds",
        json={
            "course_id": course["id"],
            "player_name": player_name,
            "tee_set_id": course["tee_sets"][0]["id"],
            "played_on": played_on,
            "scores": [
                {"hole_number": index + 1, "strokes": score}
                for index, score in enumerate(strokes)
            ],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_get_api_course_includes_nested_rounds(client: TestClient) -> None:
    course = create_course(client)
    created_round = create_round(client, course, "Ada Lovelace", [4, 5])

    response = client.get(f"/api/courses/{course['id']}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == course["id"]
    assert payload["total_par"] == 8
    assert payload["holes"] == course["holes"]
    assert len(payload["rounds"]) == 1
    nested_round = payload["rounds"][0]
    assert nested_round["id"] == created_round["id"]
    assert nested_round["player_name"] == "Ada Lovelace"
    assert nested_round["total_strokes"] == 9
    assert [score["strokes"] for score in nested_round["scores"]] == [4, 5]


def test_leaderboard_ranks_players_by_average_score(client: TestClient) -> None:
    course = create_course(client)
    create_round(client, course, "Ada Lovelace", [4, 4], played_on="2026-05-01")
    create_round(client, course, "Ada Lovelace", [3, 4], played_on="2026-05-02")
    create_round(client, course, "Grace Hopper", [5, 5], played_on="2026-05-03")

    response = client.get("/api/stats/leaderboard")

    assert response.status_code == 200
    leaderboard = response.json()
    assert [entry["player_name"] for entry in leaderboard] == ["Ada Lovelace", "Grace Hopper"]
    assert leaderboard[0]["rank"] == 1
    assert leaderboard[0]["rounds_played"] == 2
    assert leaderboard[0]["average_score"] == 7.5
    assert leaderboard[0]["best_score"] == 7
    assert leaderboard[1]["rank"] == 2
    assert leaderboard[1]["average_score"] == 10.0


def test_delete_api_round_removes_round_and_scores(client: TestClient) -> None:
    course = create_course(client)
    created_round = create_round(client, course, "Ada Lovelace", [4, 5])

    delete_response = client.delete(f"/api/rounds/{created_round['id']}")

    assert delete_response.status_code == 204
    assert delete_response.content == b""
    assert client.get(f"/api/rounds/{created_round['id']}").status_code == 404
    course_response = client.get(f"/api/courses/{course['id']}")
    assert course_response.status_code == 200
    assert course_response.json()["rounds"] == []


def test_delete_api_course_cascades_to_rounds(client: TestClient) -> None:
    course = create_course(client)
    created_round = create_round(client, course, "Ada Lovelace", [4, 5])

    delete_response = client.delete(f"/api/courses/{course['id']}")

    assert delete_response.status_code == 204
    assert delete_response.content == b""
    assert client.get(f"/api/courses/{course['id']}").status_code == 404
    assert client.get(f"/api/rounds/{created_round['id']}").status_code == 404
    assert client.get("/api/rounds").json() == []


def test_delete_missing_resources_return_404(client: TestClient) -> None:
    round_response = client.delete("/api/rounds/999")
    course_response = client.delete("/api/courses/999")

    assert round_response.status_code == 404
    assert round_response.json()["detail"] == "round not found"
    assert course_response.status_code == 404
    assert course_response.json()["detail"] == "course not found"


def test_cors_allows_nextjs_frontend_origin(client: TestClient) -> None:
    response = client.options(
        "/api/courses/1",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
