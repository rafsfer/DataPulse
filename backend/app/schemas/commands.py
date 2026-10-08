from typing import Literal

from pydantic import BaseModel, Field


class RunRequest(BaseModel):
    volume: int = Field(default=1000, ge=100, le=100000)
    seed: int = Field(default=42, ge=0, le=2147483647)
    fail_at: Literal["validation"] | None = None
