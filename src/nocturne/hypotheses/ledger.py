"""Hypothesis ledger — confidence-scored cross-thread insights from the REM stage.

A candidate insight is proposed by REM, accrues confidence when REM re-proposes it (more evidence
across nights), and is *promoted* to confirmed once confidence crosses a threshold. Nothing here
uses ground truth — confirmation is emergent from the model re-finding the connection as the
confirming evidence enters memory. The night-15 -> night-22 promotion is the demo's best moment.
"""
from __future__ import annotations

import uuid

from pydantic import BaseModel, Field

CONFIRM_THRESHOLD = 0.7
_STOP = {"the", "a", "an", "of", "to", "and", "is", "in", "on", "for", "that", "this",
         "it", "as", "at", "by", "be", "are", "from", "with", "so", "not"}


def _tokens(s: str) -> set[str]:
    return {w for w in "".join(c.lower() if c.isalnum() else " " for c in s).split()
            if len(w) > 2 and w not in _STOP}


def _similar(a: str, b: str, thresh: float = 0.3) -> bool:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return False
    return len(ta & tb) / len(ta | tb) >= thresh


class Hypothesis(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    statement: str
    confidence: float = 0.3
    support_ids: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    status: str = "open"          # open | confirmed
    proposed_night: int = 0
    confirmed_night: int | None = None


class Ledger(BaseModel):
    hypotheses: list[Hypothesis] = Field(default_factory=list)

    def propose(self, *, statement: str, confidence: float, support_ids: list[str],
                tags: list[str], night: int) -> Hypothesis:
        # Merge into an existing open hypothesis if it's the same idea.
        for h in self.hypotheses:
            if _similar(h.statement, statement):
                if confidence >= CONFIRM_THRESHOLD:
                    # Strong, evidence-backed re-proposal -> can cross the confirmation bar.
                    h.confidence = max(h.confidence, confidence)
                else:
                    # Mere repetition reinforces slightly but cannot, on its own, confirm.
                    h.confidence = min(CONFIRM_THRESHOLD - 0.05, max(h.confidence, confidence) + 0.04)
                h.support_ids = sorted(set(h.support_ids) | set(support_ids))
                if h.status == "open" and h.confidence >= CONFIRM_THRESHOLD:
                    h.status = "confirmed"
                    h.confirmed_night = night
                return h
        h = Hypothesis(statement=statement, confidence=confidence, support_ids=support_ids,
                       tags=tags, proposed_night=night)
        if h.confidence >= CONFIRM_THRESHOLD:
            h.status = "confirmed"
            h.confirmed_night = night
        self.hypotheses.append(h)
        return h

    def confirmed(self) -> list[Hypothesis]:
        return [h for h in self.hypotheses if h.status == "confirmed"]

    def render_for_prompt(self) -> str:
        if not self.hypotheses:
            return "(no hypotheses yet)"
        return "\n".join(
            f"- [{h.status}, conf={h.confidence:.2f}] {h.statement}"
            for h in sorted(self.hypotheses, key=lambda x: x.confidence, reverse=True)
        )

    def snapshot(self) -> dict:
        return {"hypotheses": [h.model_dump() for h in self.hypotheses]}
