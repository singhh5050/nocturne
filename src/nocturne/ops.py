"""The structured-rewrite primitive, shared by memory and policy.

This is the heart of nocturne: instead of appending, the agent emits structured operations
over a *weighted-item store* — add / merge / reweight / drop. The exact same op schema and
`apply_ops` engine drive BOTH levels of sleep-time compute:

  - Level 1: MemoryStore   (what the agent knows)
  - Level 2: PolicyStore   (how the agent decides what's worth knowing)

Any store implementing `WeightedStore` can be rewritten by this engine. Keeping the logic here
(not duplicated per store) is what makes the "one primitive, two levels" claim true in code.
"""
from __future__ import annotations

from typing import Any, Literal, Protocol, Union, runtime_checkable

from pydantic import BaseModel, Field


# -- op schema ----------------------------------------------------------------

class AddOp(BaseModel):
    op: Literal["add"]
    tier: str = "in_progress"
    content: str
    weight: float = 1.0
    tags: list[str] = Field(default_factory=list)
    provenance: list[str] = Field(default_factory=list)


class MergeOp(BaseModel):
    op: Literal["merge"]
    source_ids: list[str]
    tier: str = "in_progress"
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
    reason: str = ""


MemoryOp = Union[AddOp, MergeOp, ReweightOp, DropOp]


class OpsEnvelope(BaseModel):
    ops: list[MemoryOp] = Field(default_factory=list)


# JSON schema handed to the model via output_config.format. Hand-written (not derived from the
# pydantic union) so it stays within structured-output limits and stays legible in the prompt.
OPS_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "ops": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "op": {"type": "string", "enum": ["add", "merge", "reweight", "drop"]},
                    "tier": {"type": "string", "enum": ["in_progress", "episodic", "preferences"]},
                    "content": {"type": "string"},
                    "weight": {"type": "number"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "provenance": {"type": "array", "items": {"type": "string"}},
                    "source_ids": {"type": "array", "items": {"type": "string"}},
                    "id": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["op"],
            },
        }
    },
    "required": ["ops"],
}


# -- store protocol -----------------------------------------------------------

@runtime_checkable
class WeightedStore(Protocol):
    def add(self, *, tier: str, content: str, weight: float, tags: list[str],
            provenance: list[str]) -> Any: ...
    def merge(self, *, source_ids: list[str], tier: str, content: str, weight: float,
              tags: list[str]) -> Any: ...
    def reweight(self, item_id: str, weight: float) -> bool: ...
    def drop(self, item_id: str, reason: str = "") -> bool: ...


# -- parse + apply ------------------------------------------------------------

def parse_ops(data: dict[str, Any]) -> OpsEnvelope:
    """Validate a raw dict (already JSON-parsed) into an OpsEnvelope.

    Unknown / malformed individual ops are skipped rather than failing the whole batch.
    """
    raw = data.get("ops", []) if isinstance(data, dict) else []
    ops: list[MemoryOp] = []
    by_kind = {"add": AddOp, "merge": MergeOp, "reweight": ReweightOp, "drop": DropOp}
    for item in raw:
        if not isinstance(item, dict):
            continue
        cls = by_kind.get(item.get("op"))
        if cls is None:
            continue
        try:
            ops.append(cls.model_validate(item))
        except Exception:  # noqa: BLE001 - skip one bad op, keep the rest
            continue
    return OpsEnvelope(ops=ops)


def apply_ops(store: WeightedStore, envelope: OpsEnvelope) -> dict[str, int]:
    """Apply ops to a store in order. Returns counts of ops that actually took effect."""
    counts = {"add": 0, "merge": 0, "reweight": 0, "drop": 0, "noop": 0}
    for op in envelope.ops:
        if isinstance(op, AddOp):
            store.add(tier=op.tier, content=op.content, weight=op.weight,
                      tags=op.tags, provenance=op.provenance)
            counts["add"] += 1
        elif isinstance(op, MergeOp):
            ok = store.merge(source_ids=op.source_ids, tier=op.tier, content=op.content,
                             weight=op.weight, tags=op.tags)
            counts["merge" if ok else "noop"] += 1
        elif isinstance(op, ReweightOp):
            counts["reweight" if store.reweight(op.id, op.weight) else "noop"] += 1
        elif isinstance(op, DropOp):
            counts["drop" if store.drop(op.id, op.reason) else "noop"] += 1
    return counts
