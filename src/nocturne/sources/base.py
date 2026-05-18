from __future__ import annotations

from abc import ABC, abstractmethod
from pydantic import BaseModel, Field


class RawItem(BaseModel):
    source: str
    title: str
    body: str
    url: str | None = None
    meta: dict = Field(default_factory=dict)


class Source(ABC):
    name: str

    @abstractmethod
    def fetch(self) -> list[RawItem]:
        ...
