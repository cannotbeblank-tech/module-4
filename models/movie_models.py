from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class MovieGenre(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: int | None = None
    name: str


class MovieSummary(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: int
    name: str
    price: int
    description: str
    image_url: HttpUrl | None = Field(default=None, alias="imageUrl")
    location: Literal["MSK", "SPB"]
    published: bool
    rating: float
    genre_id: int = Field(alias="genreId")
    created_at: datetime = Field(alias="createdAt")
    genre: MovieGenre


class MovieDetails(MovieSummary):
    reviews: list[Any] = Field(default_factory=list)


class MovieListResponse(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    movies: list[MovieSummary]
    count: int
    page: int
    page_size: int = Field(alias="pageSize")
    page_count: int = Field(alias="pageCount")


class ErrorMovieList(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    message: str | list[str]


class ErrorMovieDetails(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    message: str | list[str]


class ErrorMovieSummary(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    message: str | list[str]
