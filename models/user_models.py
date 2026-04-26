from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class UserResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    email: str
    roles: list[str]
    verified: bool | None = None


class ErrorUserResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    message: str | list[str]
