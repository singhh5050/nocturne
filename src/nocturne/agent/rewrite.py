"""Deep-consolidation stage: the LLM rewrites bounded memory with structured ops.

This is "ours" — the consolidation arm. Given the learned policy, current bounded memory, and
tonight's raw items, the model emits add/merge/reweight/drop ops, which are applied and then the
token budget is enforced. Real model cognition on a simulated input stream.
"""
from __future__ import annotations

from typing import Any

from ..llm import LLM
from ..memory.store import MemoryStore
from ..ops import OPS_JSON_SCHEMA, apply_ops, parse_ops
from ..sim.schema import RawItem
from .prompts import REWRITE_SYSTEM


def format_items(items: list[RawItem]) -> str:
    return "\n".join(f"[{it.id} | {it.source}] {it.subject} — {it.body}" for it in items)


def consolidate(
    llm: LLM,
    *,
    store: MemoryStore,
    new_items: list[RawItem],
    policy_render: str,
    model: str | None = None,
    effort: str = "medium",
) -> dict[str, int]:
    """One night's deep consolidation. Returns op counts (with eviction count appended)."""
    user = (
        f"LEARNED POLICY:\n{policy_render}\n\n"
        f"CURRENT MEMORY:\n{store.render_for_prompt()}\n\n"
        f"NEW ITEMS tonight:\n{format_items(new_items) or '(none)'}\n\n"
        "Emit the JSON ops object now."
    )
    data = llm.complete_json(system=REWRITE_SYSTEM, user=user, schema=OPS_JSON_SCHEMA,
                             model=model, effort=effort, max_tokens=2048)
    envelope = parse_ops(data)
    counts = apply_ops(store, envelope)
    counts["evicted"] = len(store.enforce_budget())
    return counts
