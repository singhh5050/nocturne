"""Sleep-time memory rewrite: the centerpiece module.

Given the current memory store, the new raw items pulled tonight, and the nightly agent's
reasoning, ask Claude to emit *structured operations* over the memory store — not prose.

The output is a JSON object {"ops": [...]} where each op is one of:
  - add       : insert a new item into a tier
  - merge     : consolidate multiple existing items + new evidence into one
  - reweight  : adjust the salience of an existing item
  - drop      : remove an item that's gone stale or resolved

This module parses those ops with pydantic and applies them to a MemoryStore.
"""
from __future__ import annotations

import json
import re
from typing import Any, Literal, Union

from pydantic import BaseModel, Field, ValidationError

from .prompts import REWRITE_SYSTEM
from ..memory.store import MemoryStore, Tier
from ..sources.base import RawItem


class AddOp(BaseModel):
    op: Literal["add"]
    tier: Tier
    content: str
    weight: float = 1.0
    tags: list[str] = Field(default_factory=list)


class MergeOp(BaseModel):
    op: Literal["merge"]
    source_ids: list[str]
    tier: Tier
    content: str
    weight: float = 1.0
    tags: list[str] = Field(default_factory=list)


class ReweightOp(BaseModel):
    op: Literal["reweight"]
    id: str
    weight: float


class DropOp(BaseModel):
    op: Literal["drop"]
    id: str


MemoryOp = Union[AddOp, MergeOp, ReweightOp, DropOp]


class OpsEnvelope(BaseModel):
    ops: list[MemoryOp] = Field(default_factory=list)


def _extract_json(text: str) -> str:
    """Strip markdown fences if the model wrapped its output despite instructions."""
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        return fence.group(1)
    brace = text.find("{")
    if brace >= 0:
        return text[brace:]
    return text


def parse_ops(raw: str) -> OpsEnvelope:
    data = json.loads(_extract_json(raw))
    return OpsEnvelope.model_validate(data)


def apply_ops(store: MemoryStore, envelope: OpsEnvelope) -> dict[str, int]:
    """Apply ops to the store in order. Returns a count of applied ops by type."""
    counts = {"add": 0, "merge": 0, "reweight": 0, "drop": 0, "skipped": 0}
    for op in envelope.ops:
        if isinstance(op, AddOp):
            store.add(tier=op.tier, content=op.content, weight=op.weight, tags=op.tags)
            counts["add"] += 1
        elif isinstance(op, MergeOp):
            result = store.merge(
                source_ids=op.source_ids,
                tier=op.tier,
                content=op.content,
                weight=op.weight,
                tags=op.tags,
            )
            counts["merge"] += 1 if result else 0
        elif isinstance(op, ReweightOp):
            counts["reweight"] += 1 if store.reweight(op.id, op.weight) else 0
        elif isinstance(op, DropOp):
            counts["drop"] += 1 if store.drop(op.id) else 0
        else:
            counts["skipped"] += 1
    return counts


def _format_items(items: list[RawItem]) -> str:
    return "\n".join(
        f"[{it.source}] {it.title}\n  {it.body}" for it in items
    )


def rewrite_memory(
    client: Any,
    *,
    model: str,
    store: MemoryStore,
    new_items: list[RawItem],
    nightly_reasoning: str,
) -> tuple[OpsEnvelope, dict[str, int]]:
    """Ask Claude for memory ops, parse, and apply. Returns (envelope, apply_counts)."""
    user_msg = (
        f"CURRENT_MEMORY:\n{store.render_for_prompt()}\n\n"
        f"NEW_ITEMS:\n{_format_items(new_items)}\n\n"
        f"NIGHTLY_REASONING:\n{nightly_reasoning or '(none)'}\n\n"
        "Emit the JSON ops object now."
    )

    resp = client.messages_create(
        model=model,
        max_tokens=2048,
        system=REWRITE_SYSTEM,
        messages=[{"role": "user", "content": user_msg}],
    )

    text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")

    try:
        envelope = parse_ops(text)
    except (json.JSONDecodeError, ValidationError) as e:
        # Defensive: if the model returns garbage, apply nothing rather than crashing the cycle.
        envelope = OpsEnvelope(ops=[])

    counts = apply_ops(store, envelope)
    return envelope, counts
