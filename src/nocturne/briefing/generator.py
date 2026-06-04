"""Turn post-rewrite memory + hypothesis ledger into a proactive morning briefing."""
from __future__ import annotations

from ..hypotheses.ledger import Ledger
from ..llm import LLM
from ..memory.store import MemoryStore
from ..agent.prompts import BRIEFING_SYSTEM


def generate_briefing(
    llm: LLM, *, store: MemoryStore, ledger: Ledger, night: int,
    model: str | None = None, effort: str = "low",
) -> str:
    """LLM-written proactive briefing. Falls back to a deterministic render on empty output."""
    user = (
        f"Night {night} memory (post-rewrite):\n{store.render_for_prompt()}\n\n"
        f"Hypothesis ledger:\n{ledger.render_for_prompt()}\n\n"
        "Write the morning briefing now."
    )
    text = llm.complete(system=BRIEFING_SYSTEM, user=user, model=model, effort=effort,
                        max_tokens=1024).strip()
    return text or render_briefing(store, ledger, night)


def render_briefing(store: MemoryStore, ledger: Ledger, night: int) -> str:
    """Deterministic markdown briefing (no API) — used as a fallback and in tests."""
    lines = [f"# Morning briefing — night {night}", ""]
    in_prog = store.by_tier("in_progress")
    if in_prog:
        lines.append("## What's open")
        for it in in_prog[:5]:
            tags = f" _({', '.join(it.tags)})_" if it.tags else ""
            lines.append(f"- {it.content}{tags}")
        lines.append("")
    for h in ledger.confirmed()[:2]:
        lines.append(f"**Overnight idea:** {h.statement}")
    prefs = store.by_tier("preferences")
    if prefs:
        lines.append("\n## Standing context")
        for it in prefs[:3]:
            lines.append(f"- {it.content}")
    if len(lines) <= 2:
        lines.append("_Nothing notable from last night._")
    return "\n".join(lines).rstrip() + "\n"
