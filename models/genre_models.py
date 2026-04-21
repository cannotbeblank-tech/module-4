from __future__ import annotations

from pydantic import BaseModel, ConfigDict, RootModel


class GenreResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    name: str


class GenreListResponse(RootModel[list[GenreResponse]]):
    pass
