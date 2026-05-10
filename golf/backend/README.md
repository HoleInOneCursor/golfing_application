# Golf Backend

FastAPI backend for golf courses and rounds. Data is stored in SQLite via
SQLAlchemy, with tables created automatically on application startup.

## Install

```bash
cd golf/backend
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

## Configure

The API uses `golf/backend/golf.db` by default. To use a different database URL:

```bash
export GOLF_DATABASE_URL=sqlite:////absolute/path/to/golf.db
```

## Run

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8787
```

## Endpoints

- `GET /health`
- `GET /api/courses`
- `POST /api/courses`
- `GET /api/rounds`
- `GET /api/rounds?course_id=1`
- `POST /api/rounds`
