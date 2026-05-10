from __future__ import annotations

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models  # noqa: F401
from .database import Base, engine
from .routers import courses, rounds


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Golf Backend API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(courses.router)
app.include_router(rounds.router)



@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
