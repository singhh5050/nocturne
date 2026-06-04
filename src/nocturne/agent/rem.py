"""REM stage: cross-thread synthesis -> hypothesis ledger."""
from __future__ import annotations

from ..hypotheses.ledger import Ledger
from ..llm import LLM
from ..memory.store import MemoryStore
from .prompts import REM_SYSTEM

REM_JSON_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "hypotheses": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "statement": {"type": "string"},
                    "confidence": {"type": "number"},
                    "support_ids": {"type": "array", "items": {"type": "string"}},
                    "tags": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["statement", "confidence"],
            },
        }
    },
    "required": ["hypotheses"],
}


def rem_synthesize(
    llm: LLM, *, store: MemoryStore, ledger: Ledger, night: int,
    model: str | None = None, effort: str = "medium",
) -> list[str]:
    """Look across memory for latent cross-thread links; record them in the ledger."""
    if len(store.items) < 3:
        return []
    user = f"MEMORY:\n{store.render_for_prompt()}\n\nEmit the JSON hypotheses object now."
    data = llm.complete_json(system=REM_SYSTEM, user=user, schema=REM_JSON_SCHEMA,
                             model=model, effort=effort, max_tokens=1024)
    proposed: list[str] = []
    for h in data.get("hypotheses", []) or []:
        if not isinstance(h, dict) or not h.get("statement"):
            continue
        ledger.propose(
            statement=str(h["statement"]),
            confidence=float(h.get("confidence", 0.3) or 0.3),
            support_ids=[str(x) for x in (h.get("support_ids") or [])],
            tags=[str(x) for x in (h.get("tags") or [])],
            night=night,
        )
        proposed.append(str(h["statement"]))
    return proposed
