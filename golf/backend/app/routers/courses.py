from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Course
from ..schemas import CourseCreate, CourseRead

router = APIRouter(prefix="/api/courses", tags=["courses"])


@router.get("", response_model=list[CourseRead])
def list_courses(db: Session = Depends(get_db)) -> list[Course]:
    return list(db.scalars(select(Course).order_by(Course.id)))


@router.post("", response_model=CourseRead, status_code=status.HTTP_201_CREATED)
def create_course(course_in: CourseCreate, db: Session = Depends(get_db)) -> Course:
    course = Course(**course_in.model_dump())
    db.add(course)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="course name already exists") from exc

    db.refresh(course)
    return course
