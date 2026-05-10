from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Course, Round
from ..schemas import RoundCreate, RoundRead

router = APIRouter(prefix="/api/rounds", tags=["rounds"])


@router.get("", response_model=list[RoundRead])
def list_rounds(db: Session = Depends(get_db)) -> list[Round]:
    return list(db.scalars(select(Round).order_by(Round.id)))


@router.post("", response_model=RoundRead, status_code=status.HTTP_201_CREATED)
def create_round(round_in: RoundCreate, db: Session = Depends(get_db)) -> Round:
    course = db.get(Course, round_in.course_id)
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="course not found",
        )

    round_obj = Round(**round_in.model_dump())
    db.add(round_obj)
    db.commit()
    db.refresh(round_obj)
    return round_obj


@router.get("/{round_id}", response_model=RoundRead)
def get_round(round_id: int, db: Session = Depends(get_db)) -> Round:
    round_obj = db.get(Round, round_id)
    if round_obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="round not found",
        )
    return round_obj
