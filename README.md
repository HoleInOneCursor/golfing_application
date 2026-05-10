# golfing_application

Minimal dashboard with a full-stack golf score tracker.

## Features

- Next.js dashboard with the golf tracker at `/golf`
- FastAPI API on port `8787`
- SQLite persistence for courses, holes/par, rounds, and per-hole scores

## Requirements

- Node.js and npm
- Python 3.10+

## Install the dashboard

```bash
npm install
```

## Run the backend API

```bash
cd golf/backend
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8787
```

The API stores data in `golf/backend/golf.db` by default.

Optional API environment variables:

- `GOLF_DATABASE_URL`: SQLAlchemy database URL. Defaults to the local SQLite database.

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
- `GET /api/courses`
- `POST /api/courses`
- `GET /api/rounds`
- `POST /api/rounds`
- `GET /api/rounds/{round_id}`
- `POST /api/rounds/{round_id}/scores`
