from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_db, init_db
from .models import Course, Round
from .schemas import CourseCreate, CourseResponse, RoundCreate, RoundResponse


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    init_db()
    yield


app = FastAPI(title="Golf Backend API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/courses", response_model=list[CourseResponse], tags=["courses"])
def list_courses(db: Session = Depends(get_db)) -> list[Course]:
    return list(db.scalars(select(Course).order_by(Course.id)))


@app.post(
    "/api/courses",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["courses"],
)
def create_course(course_in: CourseCreate, db: Session = Depends(get_db)) -> Course:
    course = Course(**course_in.model_dump())
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


@app.get("/api/rounds", response_model=list[RoundResponse], tags=["rounds"])
def list_rounds(
    course_id: int | None = Query(default=None, ge=1),
    db: Session = Depends(get_db),
) -> list[Round]:
    statement = select(Round)
    if course_id is not None:
        statement = statement.where(Round.course_id == course_id)
    statement = statement.order_by(Round.date_played.desc(), Round.id.desc())
    return list(db.scalars(statement))


@app.post(
    "/api/rounds",
    response_model=RoundResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["rounds"],
)
def create_round(round_in: RoundCreate, db: Session = Depends(get_db)) -> Round:
    course = db.get(Course, round_in.course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="course not found")

    round_obj = Round(**round_in.model_dump())
    db.add(round_obj)
    db.commit()
    db.refresh(round_obj)
    return round_obj
