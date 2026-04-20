from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class MovieGenre(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int | None = None
    name: str


class MovieSummary(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    name: str
    price: int
    description: str
    imageUrl: HttpUrl | None = None
    location: Literal["MSK", "SPB"]
    published: bool
    rating: int
    genreId: int
    createdAt: datetime
    genre: MovieGenre


class MovieDetails(MovieSummary):
    reviews: list[Any] = Field(default_factory=list)


class MovieListResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    movies: list[MovieSummary]
    count: int
    page: int
    pageSize: int
    pageCount: int
