"""PolicyStore — the agent's editable operating policy (Level 2).

A set of weighted directives ("lessons") that are prepended to the memory-rewrite system prompt.
Each morning, after a graded critique of yesterday's briefing, the agent rewrites THIS store with
the very same add/merge/reweight/drop primitive it uses on episodic memory. That is the
self-improvement loop: the agent edits how it decides what's worth knowing.

Implements WeightedStore so ops.apply_ops drives it unchanged.
"""
from __future__ import annotations

import re
import uuid

from pydantic import BaseModel, Field

_STOP = {"the", "a", "an", "of", "to", "and", "is", "in", "on", "for", "that", "it", "items"}


def _toks(s: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", s.lower()) if len(w) > 2 and w not in _STOP}


def _similar(a: str, b: str, thresh: float = 0.55) -> bool:
    ta, tb = _toks(a), _toks(b)
    if not ta or not tb:
        return False
    return len(ta & tb) / len(ta | tb) >= thresh


class Directive(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    content: str
    weight: float = 1.0
    learned_night: int = 0


class PolicyStore(BaseModel):
    directives: dict[str, Directive] = Field(default_factory=dict)
    current_night: int = 0
    max_directives: int = 12

    # -- WeightedStore protocol (tier/provenance accepted and ignored) --------

    def add(self, *, tier: str = "", content: str, weight: float = 1.0,
            tags: list[str] | None = None, provenance: list[str] | None = None) -> Directive:
        # Dedup: if the agent re-learns a directive it already holds, reinforce it instead of
        # accumulating duplicates (keeps the policy small and legible).
        for d in self.directives.values():
            if _similar(d.content, content):
                d.weight = min(2.5, max(d.weight, weight) + 0.1)
                return d
        d = Directive(content=content, weight=weight, learned_night=self.current_night)
        self.directives[d.id] = d
        self._prune()
        return d

    def merge(self, *, source_ids: list[str], tier: str = "", content: str,
              weight: float = 1.0, tags: list[str] | None = None) -> Directive | None:
        for sid in source_ids:
            self.directives.pop(sid, None)
        d = self.add(content=content, weight=weight)
        return d

    def reweight(self, item_id: str, weight: float) -> bool:
        d = self.directives.get(item_id)
        if not d:
            return False
        d.weight = weight
        return True

    def drop(self, item_id: str, reason: str = "") -> bool:
        return self.directives.pop(item_id, None) is not None

    # -- helpers --------------------------------------------------------------

    def _prune(self) -> None:
        # Keep the policy compact — drop the weakest directives past the cap.
        while len(self.directives) > self.max_directives:
            victim = min(self.directives.values(), key=lambda d: d.weight)
            self.directives.pop(victim.id, None)

    def ranked(self) -> list[Directive]:
        return sorted(self.directives.values(), key=lambda d: d.weight, reverse=True)

    def render_for_prompt(self) -> str:
        if not self.directives:
            return "(no learned directives yet)"
        return "\n".join(
            f"- ({d.id}, w={d.weight:.2f}) {d.content}" for d in self.ranked()
        )

    def clone(self) -> "PolicyStore":
        return PolicyStore.model_validate(self.model_dump())

    def snapshot(self) -> dict:
        return {"night": self.current_night,
                "directives": [d.model_dump() for d in self.ranked()]}

    @classmethod
    def seed(cls) -> "PolicyStore":
        """A deliberately NAIVE starting policy, so the agent has real room to learn.

        It says nothing about dropping noise, retaining deadlines, or reconciling — those are the
        judgments the self-improvement loop must discover from the graded morning critiques. A
        static policy frozen here will keep almost everything and bloat; a self-improving one learns
        to be selective. That gap is the experiment."""
        s = cls()
        s.add(content="You are new here and have not yet learned what matters to this researcher; "
                      "when unsure, keep the item.", weight=0.5)
        return s
