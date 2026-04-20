from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class GenreResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    name: str
