from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


Tier = Literal["in_progress", "episodic", "preferences"]


class MemoryItem(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    tier: Tier
    content: str
    weight: float = 1.0
    tags: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class MemoryStore(BaseModel):
    items: dict[str, MemoryItem] = Field(default_factory=dict)

    def add(self, tier: Tier, content: str, weight: float = 1.0, tags: list[str] | None = None) -> MemoryItem:
        item = MemoryItem(tier=tier, content=content, weight=weight, tags=tags or [])
        self.items[item.id] = item
        return item

    def get(self, item_id: str) -> MemoryItem | None:
        return self.items.get(item_id)

    def drop(self, item_id: str) -> bool:
        return self.items.pop(item_id, None) is not None

    def reweight(self, item_id: str, weight: float) -> bool:
        item = self.items.get(item_id)
        if not item:
            return False
        item.weight = weight
        item.updated_at = datetime.now(timezone.utc).isoformat()
        return True

    def merge(self, source_ids: list[str], tier: Tier, content: str, weight: float = 1.0, tags: list[str] | None = None) -> MemoryItem | None:
        merged_tags = set(tags or [])
        for sid in source_ids:
            existing = self.items.get(sid)
            if existing:
                merged_tags.update(existing.tags)
        for sid in source_ids:
            self.items.pop(sid, None)
        return self.add(tier=tier, content=content, weight=weight, tags=sorted(merged_tags))

    def by_tier(self, tier: Tier) -> list[MemoryItem]:
        return sorted(
            (i for i in self.items.values() if i.tier == tier),
            key=lambda i: i.weight,
            reverse=True,
        )

    def render_for_prompt(self) -> str:
        lines = []
        for tier in ("preferences", "in_progress", "episodic"):
            items = self.by_tier(tier)  # type: ignore[arg-type]
            if not items:
                continue
            lines.append(f"## {tier}")
            for it in items:
                tags = f" [{','.join(it.tags)}]" if it.tags else ""
                lines.append(f"- ({it.id}, w={it.weight:.2f}){tags} {it.content}")
        return "\n".join(lines) if lines else "(empty memory)"

    @classmethod
    def load(cls, path: str | Path) -> MemoryStore:
        p = Path(path)
        if not p.exists():
            return cls()
        return cls.model_validate_json(p.read_text())

    def save(self, path: str | Path) -> None:
        Path(path).write_text(self.model_dump_json(indent=2))
