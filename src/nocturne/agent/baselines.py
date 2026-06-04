"""Baseline memory policies — the named foils for the brains comparison.

All arms expose the same interface: ingest(night, items) -> render() / total_tokens() / snapshot().
These baselines are deliberately *mechanical* (no LLM): the experiment contrasts mechanical
accumulation vs. LLM-driven consolidation (ours, in agent/rewrite.py). Every arm answers the same
QA questions with the same model given ITS memory, so the comparison is fair.

  - append           : store every item as a line, never drop, no budget (grows fastest).
  - gbrain_accumulate: GBrain-style library — group items into per-thread "pages", dedup exact
                       repeats, but never forget. Grows with the number of distinct facts.
  - window           : keep only the last K items (sliding-window / last-K).
"""
from __future__ import annotations

from ..sim.schema import RawItem


def _approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)


class AppendArm:
    name = "append"

    def __init__(self) -> None:
        self.lines: list[str] = []

    def ingest(self, night: int, items: list[RawItem]) -> None:
        for it in items:
            self.lines.append(f"[{it.source}] {it.subject}: {it.body}")

    def render(self) -> str:
        return "\n".join(self.lines) if self.lines else "(empty)"

    def total_tokens(self) -> int:
        return _approx_tokens(self.render())

    def item_count(self) -> int:
        return len(self.lines)

    def snapshot(self) -> dict:
        return {"arm": self.name, "items": self.item_count(), "tokens": self.total_tokens()}


class GBrainArm:
    """An accumulate-everything library: per-thread pages, dedup exact repeats, never forget."""
    name = "gbrain_accumulate"

    def __init__(self) -> None:
        self.pages: dict[str, list[str]] = {}

    def ingest(self, night: int, items: list[RawItem]) -> None:
        for it in items:
            line = f"{it.subject}: {it.body}"
            page = self.pages.setdefault(it.thread, [])
            if line not in page:  # dedup exact repeats, but keep every distinct fact forever
                page.append(line)

    def render(self) -> str:
        if not self.pages:
            return "(empty)"
        out = []
        for thread in sorted(self.pages):
            out.append(f"# {thread}")
            out.extend(f"- {ln}" for ln in self.pages[thread])
        return "\n".join(out)

    def total_tokens(self) -> int:
        return _approx_tokens(self.render())

    def item_count(self) -> int:
        return sum(len(v) for v in self.pages.values())

    def snapshot(self) -> dict:
        return {"arm": self.name, "items": self.item_count(), "tokens": self.total_tokens(),
                "threads": len(self.pages)}


class WindowArm:
    name = "window"

    def __init__(self, k: int = 40) -> None:
        self.k = k
        self.lines: list[str] = []

    def ingest(self, night: int, items: list[RawItem]) -> None:
        for it in items:
            self.lines.append(f"[{it.source}] {it.subject}: {it.body}")
        self.lines = self.lines[-self.k:]

    def render(self) -> str:
        return "\n".join(self.lines) if self.lines else "(empty)"

    def total_tokens(self) -> int:
        return _approx_tokens(self.render())

    def item_count(self) -> int:
        return len(self.lines)

    def snapshot(self) -> dict:
        return {"arm": self.name, "items": self.item_count(), "tokens": self.total_tokens()}


def make_baseline(name: str):
    if name == "append":
        return AppendArm()
    if name == "gbrain_accumulate":
        return GBrainArm()
    if name == "window":
        return WindowArm()
    raise ValueError(f"unknown baseline arm: {name}")
