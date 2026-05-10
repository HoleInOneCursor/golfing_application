# golfing_application

Minimal dashboard with a full-stack golf score tracker.

## Features

- Next.js dashboard with the golf tracker at `/golf`
- FastAPI API on port `8787`
- SQLite persistence for courses, holes/par, rounds, and per-hole scores

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

The API stores data in `golf_scores.db` by default.

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
- `GET /courses`
- `POST /courses`
- `GET /courses/{course_id}`
- `GET /rounds`
- `POST /rounds`
- `GET /rounds/{round_id}`
- `PUT /rounds/{round_id}/scores/{hole_number}`
