from __future__ import annotations

from datetime import date as date_type

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
    score: int = Field(ge=0)
    date_played: date_type


class RoundRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    player_name: str
    score: int
    date_played: date_type
