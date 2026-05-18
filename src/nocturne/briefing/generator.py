"""Turn post-rewrite memory state into a markdown morning briefing."""
from __future__ import annotations

from ..memory.store import MemoryStore


def generate_briefing(store: MemoryStore) -> str:
    lines: list[str] = ["# Morning briefing", ""]

    in_prog = store.by_tier("in_progress")
    if in_prog:
        lines.append("## What's open")
        for item in in_prog[:5]:
            tags = f" _({', '.join(item.tags)})_" if item.tags else ""
            lines.append(f"- {item.content}{tags}")
        lines.append("")

    episodic = store.by_tier("episodic")
    if episodic:
        lines.append("## Recent context")
        for item in episodic[:3]:
            lines.append(f"- {item.content}")
        lines.append("")

    prefs = store.by_tier("preferences")
    if prefs:
        lines.append("## Standing preferences")
        for item in prefs[:3]:
            lines.append(f"- {item.content}")
        lines.append("")

    if len(lines) <= 2:
        lines.append("_Nothing notable from last night._")

    return "\n".join(lines).rstrip() + "\n"
