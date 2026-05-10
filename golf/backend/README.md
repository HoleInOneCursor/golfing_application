# Golf Backend

FastAPI backend for golf courses and rounds. Data is stored in a local SQLite
database at `golf/backend/golf.db`, and tables are created automatically on
application startup with SQLAlchemy metadata.

## Install

```bash
cd golf/backend
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
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
- `POST /api/rounds`
- `GET /api/rounds/{id}`
