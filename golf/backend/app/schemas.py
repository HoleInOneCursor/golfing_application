from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class CourseCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=120)
    location: str = Field(min_length=1, max_length=120)
    holes: int = Field(ge=1, le=18)
    par: int = Field(ge=1, le=100)


class CourseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    location: str
    holes: int
    par: int


class RoundCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    course_id: int = Field(ge=1)
    player_name: str = Field(min_length=1, max_length=120)
    date: date | None = None


class HoleScoreCreate(BaseModel):
    hole_number: int = Field(ge=1, le=18)
    strokes: int = Field(ge=1, le=30)


class HoleScoreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    round_id: int
    hole_number: int
    strokes: int


class RoundRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    player_name: str
    date: date
    total_score: int


class RoundDetail(RoundRead):
    hole_scores: list[HoleScoreRead]
