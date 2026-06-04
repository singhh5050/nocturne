"""MemoryStore — the bounded, evolving working memory (Level 1).

Design bets (the opposite of an accumulate-everything library like GBrain):
  - Hard token budget: memory MUST stay under a cap, so rewrite has to make real tradeoffs.
  - Active forgetting: weight decays each night; silence fades, re-mention reinforces.
  - Provenance: every item links to the raw items that produced it ("why do you believe this?").
  - Three tiers: preferences (durable) / in_progress (active work) / episodic (one-off).

Implements the WeightedStore protocol from ops.py, so the shared rewrite engine drives it.
"""
from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, Field

from . import decay as decay_mod

Tier = Literal["in_progress", "episodic", "preferences"]


def _approx_tokens(text: str) -> int:
    # Cheap, deterministic token estimate (~4 chars/token) — good enough for budget enforcement.
    return max(1, len(text) // 4)


class MemoryItem(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    tier: Tier = "in_progress"
    content: str
    weight: float = 1.0
    tags: list[str] = Field(default_factory=list)
    provenance: list[str] = Field(default_factory=list)  # raw item ids this was derived from
    created_night: int = 0
    last_reinforced_night: int = 0

    @property
    def tokens(self) -> int:
        return _approx_tokens(self.content)


class MemoryStore(BaseModel):
    items: dict[str, MemoryItem] = Field(default_factory=dict)
    token_budget: int = 1200
    current_night: int = 0
    # ids dropped because they fell out of budget (for failure analysis / the dashboard).
    evicted: list[str] = Field(default_factory=list)

    # -- WeightedStore protocol ----------------------------------------------

    def add(self, *, tier: str = "in_progress", content: str, weight: float = 1.0,
            tags: list[str] | None = None, provenance: list[str] | None = None) -> MemoryItem:
        item = MemoryItem(
            tier=tier, content=content, weight=weight, tags=tags or [],
            provenance=provenance or [],
            created_night=self.current_night, last_reinforced_night=self.current_night,
        )
        self.items[item.id] = item
        return item

    def merge(self, *, source_ids: list[str], tier: str = "in_progress", content: str,
              weight: float = 1.0, tags: list[str] | None = None) -> MemoryItem | None:
        merged_tags = set(tags or [])
        merged_prov: list[str] = []
        found_any = False
        for sid in source_ids:
            existing = self.items.get(sid)
            if existing:
                found_any = True
                merged_tags.update(existing.tags)
                merged_prov.extend(existing.provenance)
        for sid in source_ids:
            self.items.pop(sid, None)
        item = self.add(tier=tier, content=content, weight=weight,
                        tags=sorted(merged_tags), provenance=merged_prov)
        return item if found_any else item  # merge of unknown ids still adds the consolidated item

    def reweight(self, item_id: str, weight: float) -> bool:
        it = self.items.get(item_id)
        if not it:
            return False
        it.weight = weight
        it.last_reinforced_night = self.current_night
        return True

    def drop(self, item_id: str, reason: str = "") -> bool:
        return self.items.pop(item_id, None) is not None

    # -- nightly maintenance --------------------------------------------------

    def advance_night(self, night: int, half_life: float = decay_mod.DEFAULT_HALF_LIFE) -> None:
        """Apply decay to every item based on nights since last reinforcement, then set the clock."""
        for it in self.items.values():
            elapsed = night - it.last_reinforced_night
            it.weight = decay_mod.decayed_weight(it.weight, elapsed, half_life)
        self.current_night = night

    def enforce_budget(self) -> list[str]:
        """Drop lowest-weight items until under the token budget. Returns dropped ids."""
        dropped: list[str] = []
        while self.total_tokens() > self.token_budget and self.items:
            victim = min(self.items.values(), key=lambda i: (i.weight, -i.tokens))
            self.items.pop(victim.id, None)
            dropped.append(victim.id)
            self.evicted.append(victim.id)
        return dropped

    # -- queries --------------------------------------------------------------

    def total_tokens(self) -> int:
        return sum(i.tokens for i in self.items.values())

    def by_tier(self, tier: str) -> list[MemoryItem]:
        return sorted((i for i in self.items.values() if i.tier == tier),
                      key=lambda i: i.weight, reverse=True)

    def ranked(self) -> list[MemoryItem]:
        return sorted(self.items.values(), key=lambda i: i.weight, reverse=True)

    def render_for_prompt(self) -> str:
        lines: list[str] = []
        for tier in ("preferences", "in_progress", "episodic"):
            tier_items = self.by_tier(tier)
            if not tier_items:
                continue
            lines.append(f"## {tier}")
            for it in tier_items:
                tags = f" [{','.join(it.tags)}]" if it.tags else ""
                lines.append(f"- ({it.id}, w={it.weight:.2f}){tags} {it.content}")
        cap = f"(memory: {self.total_tokens()}/{self.token_budget} tokens)"
        return (("\n".join(lines)) if lines else "(empty memory)") + "\n" + cap

    # -- persistence ----------------------------------------------------------

    def snapshot(self) -> dict:
        """Plain-dict snapshot for run logs / the dashboard time-machine."""
        return {
            "night": self.current_night,
            "total_tokens": self.total_tokens(),
            "token_budget": self.token_budget,
            "items": [i.model_dump() for i in self.ranked()],
        }
