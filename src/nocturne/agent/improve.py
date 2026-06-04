"""Self-improvement stage: rewrite the agent's own policy from a graded critique.

The same add/merge/reweight/drop primitive used on memory, applied to the PolicyStore. The
validation-gated hill-climb (keep-best + rollback) lives in the harness, which calls this to
propose an edit and then decides whether to keep it.
"""
from __future__ import annotations

from ..llm import LLM
from ..ops import OPS_JSON_SCHEMA, apply_ops, parse_ops
from ..policy.store import PolicyStore
from .prompts import IMPROVE_SYSTEM


def improve_policy(
    llm: LLM, *, policy: PolicyStore, critique: str,
    model: str | None = None, effort: str = "medium",
) -> dict[str, int]:
    """Propose and apply policy ops in place. Returns op counts."""
    user = (
        f"CURRENT POLICY:\n{policy.render_for_prompt()}\n\n"
        f"CRITIQUE:\n{critique}\n\n"
        "Emit the JSON ops object that improves the policy now."
    )
    data = llm.complete_json(system=IMPROVE_SYSTEM, user=user, schema=OPS_JSON_SCHEMA,
                             model=model, effort=effort, max_tokens=1024)
    return apply_ops(policy, parse_ops(data))
