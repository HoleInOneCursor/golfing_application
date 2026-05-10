# golfing_application

Minimal dashboard with a larger full-stack golf demo flow.

## Features

- Existing Next.js dashboard entry at `/`
- Expanded golf workspace at `/golf`
- FastAPI API on port `8787`
- SQLite persistence for players, handicap-index stub data, courses, tee sets, holes/par, rounds, scores, and activity feed events
- Stableford scoring twist in round summaries and per-hole scorecards

## Demo user journey

1. Open the dashboard at `http://localhost:3000` and choose **Open golf tracker**.
2. In `/golf`, add one or more players. The handicap index is captured as stub data for the demo; net scoring is not applied yet.
3. Add a course with comma-separated hole pars and tee sets in `Name:Color:Yards` format, for example:
   `Championship:Black:6900, Member:White:6200, Forward:Gold:5200`.
4. Start a Stableford round by selecting a player, course, tee set, and optional play date.
5. Enter strokes hole by hole. The scorecard updates total strokes, score to par, completion, and Stableford points.
6. Review the activity feed, which is also available from the API at `GET /activity`.

## Requirements

- Node.js and npm
- Python 3.10+

## Install

```bash
npm install
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

## Run the API

```bash
. .venv/bin/activate
uvicorn api.main:app --reload --host 0.0.0.0 --port 8787
```

The API stores data in `golf_scores.db` by default and migrates older local demo databases in place.

Optional API environment variables:

- `GOLF_DB_PATH`: SQLite database path. Defaults to `golf_scores.db`.
- `CORS_ALLOW_ORIGINS`: comma-separated allowed origins. Defaults to `*`.

## Run the dashboard

In a second terminal:

```bash
NEXT_PUBLIC_DASHBOARD_API_BASE=http://localhost:8787 npm run dev
```

Open:

- Dashboard: `http://localhost:3000`
- Golf tracker: `http://localhost:3000/golf`

The golf tracker reads the API URL from `NEXT_PUBLIC_DASHBOARD_API_BASE`.

## API overview

- `GET /health`
- `GET /players`
- `POST /players`
- `GET /courses`
- `POST /courses`
- `GET /courses/{course_id}`
- `GET /rounds`
- `POST /rounds`
- `GET /rounds/{round_id}`
- `PUT /rounds/{round_id}/scores/{hole_number}`
- `GET /activity`
