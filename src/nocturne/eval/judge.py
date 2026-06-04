"""Build the morning critique that drives self-improvement.

Primarily objective (derived from ground-truth metrics) so the reward can't be hacked; an optional
LLM-judge of briefing quality can be layered on but is off by default to control cost.
"""
from __future__ import annotations

from ..sim.schema import WorldTrace
from . import metrics as M


def build_critique(render_text: str, num_facts: int, trace: WorldTrace, night: int) -> str:
    text = render_text.lower()
    active = M.active_needles(trace, night)
    missed = [nd for nd in active if not M._needle_present(text, nd)]
    noise_leak = text.count("safe to ignore")
    lines = [
        f"Night {night} grading of the memory/briefing:",
        f"- Important items that should be retained but were MISSING: "
        + ("; ".join(nd.description for nd in missed) if missed else "none"),
        f"- Noise items that leaked into memory: {noise_leak}",
        f"- Facts currently held in memory: {num_facts}",
    ]
    if missed:
        lines.append("  -> The policy should ensure these kinds of items are kept/consolidated.")
    if noise_leak:
        lines.append("  -> The policy should be stricter about dropping promotional/low-signal items.")
    if num_facts > 20:
        lines.append("  -> Memory is bloating; the policy should consolidate and forget more aggressively.")
    return "\n".join(lines)
