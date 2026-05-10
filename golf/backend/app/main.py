from __future__ import annotations

import os
from datetime import date

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from .database import get_db
from .models import Course, HoleScore, Round
from .schemas import (
    CourseCreate,
    CourseRead,
    HoleScoreCreate,
    RoundCreate,
    RoundDetail,
    RoundRead,
)


app = FastAPI(title="Golf Backend API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOW_ORIGINS", "*").split(","),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_round_or_404(db: Session, round_id: int) -> Round:
    round_obj = db.scalar(
        select(Round)
        .options(selectinload(Round.hole_scores), selectinload(Round.course))
        .where(Round.id == round_id)
    )
    if round_obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="round not found")
    return round_obj


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/courses", response_model=list[CourseRead], tags=["courses"])
def list_courses(db: Session = Depends(get_db)) -> list[Course]:
    return list(db.scalars(select(Course).order_by(Course.name)))


@app.post(
    "/api/courses",
    response_model=CourseRead,
    status_code=status.HTTP_201_CREATED,
    tags=["courses"],
)
def create_course(course_in: CourseCreate, db: Session = Depends(get_db)) -> Course:
    course = Course(**course_in.model_dump())
    db.add(course)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="course name already exists",
        ) from exc
    db.refresh(course)
    return course


@app.get("/api/rounds", response_model=list[RoundRead], tags=["rounds"])
def list_rounds(db: Session = Depends(get_db)) -> list[Round]:
    return list(db.scalars(select(Round).order_by(Round.date.desc(), Round.id.desc())))


@app.post(
    "/api/rounds",
    response_model=RoundRead,
    status_code=status.HTTP_201_CREATED,
    tags=["rounds"],
)
def create_round(round_in: RoundCreate, db: Session = Depends(get_db)) -> Round:
    course = db.get(Course, round_in.course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="course not found")

    round_obj = Round(
        course_id=round_in.course_id,
        player_name=round_in.player_name,
        date=round_in.date or date.today(),
        total_score=0,
    )
    db.add(round_obj)
    db.commit()
    db.refresh(round_obj)
    return round_obj


@app.get("/api/rounds/{round_id}", response_model=RoundDetail, tags=["rounds"])
def get_round(round_id: int, db: Session = Depends(get_db)) -> Round:
    return get_round_or_404(db, round_id)


@app.post(
    "/api/rounds/{round_id}/scores",
    response_model=RoundDetail,
    status_code=status.HTTP_201_CREATED,
    tags=["rounds"],
)
def add_hole_score(
    round_id: int,
    score_in: HoleScoreCreate,
    db: Session = Depends(get_db),
) -> Round:
    round_obj = get_round_or_404(db, round_id)

    if score_in.hole_number > round_obj.course.holes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="hole number is outside the course hole range",
        )

    existing_score = db.scalar(
        select(HoleScore).where(
            HoleScore.round_id == round_id,
            HoleScore.hole_number == score_in.hole_number,
        )
    )
    if existing_score is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="score already exists for this hole",
        )

    hole_score = HoleScore(
        round_id=round_id,
        hole_number=score_in.hole_number,
        strokes=score_in.strokes,
    )

    try:
        db.add(hole_score)
        db.flush()
        total_score = db.scalar(
            select(func.coalesce(func.sum(HoleScore.strokes), 0)).where(
                HoleScore.round_id == round_id
            )
        )
        round_obj.total_score = int(total_score or 0)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="score already exists for this hole",
        ) from exc

    return get_round_or_404(db, round_id)
