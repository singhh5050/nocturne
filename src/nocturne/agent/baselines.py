"""Baseline memory policies — the named foils for the brains comparison.

All arms expose: ingest(night, items) -> render() / total_tokens() / item_count().
Baselines are mechanical (no LLM); ours (agent/rewrite.py) uses LLM consolidation. Every arm
answers the same QA with the same model from ITS memory.

  - append           : store every item, never drop, dump the WHOLE store at query time (naive).
  - gbrain_accumulate: GBrain-style library — never forget, but at query time RETRIEVE the top-K
                       relevant pages and synthesize from those (mirrors GBrain's hybrid retrieval
                       + ~20-40 page gather, not a full-store dump). The fair GBrain analog.
  - window           : keep only the last K items (sliding-window / last-K).

Two cost axes are tracked so the comparison is honest:
  - store_tokens : size of everything the arm holds (storage footprint).
  - query_tokens : size of the context actually used to answer (what you pay per query).
Accumulation arms have huge storage; the *retrieval* arm keeps query cost bounded like GBrain.
"""
from __future__ import annotations

import re

from ..sim.schema import RawItem

_STOP = {"the", "a", "an", "of", "to", "and", "is", "in", "on", "for", "that", "what", "does",
         "do", "did", "was", "now", "are", "your", "you", "how", "many", "when", "who", "it"}


def _approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def _toks(s: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", s.lower()) if len(w) > 2 and w not in _STOP}


def _retrieve_topk(pages: list[str], question: str, k: int) -> list[str]:
    """Lexical top-K retrieval (a stand-in for GBrain's hybrid vector+keyword+graph retrieval)."""
    q = _toks(question)
    scored = sorted(pages, key=lambda p: len(_toks(p) & q), reverse=True)
    hits = [p for p in scored if _toks(p) & q]
    return (hits or scored)[:k]


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
    """Accumulate-everything library (never forget) + top-K retrieval at query time.

    Storage grows unbounded (like GBrain's 146K pages); but answering RETRIEVES the top-K relevant
    pages and synthesizes from those — the faithful GBrain analog (hybrid retrieve + synthesize),
    not a full-store dump. So its query cost stays bounded, and the comparison turns on what
    actually differs: contradiction handling, recall, and storage footprint."""
    name = "gbrain_accumulate"

    def __init__(self, k: int = 12) -> None:
        self.pages: list[str] = []   # every distinct fact, kept forever
        self.k = k

    def ingest(self, night: int, items: list[RawItem]) -> None:
        for it in items:
            line = f"[{it.source}] {it.subject}: {it.body}"
            if line not in self.pages:   # dedup exact repeats; never forget
                self.pages.append(line)

    def render(self) -> str:             # full store (storage footprint)
        return "\n".join(self.pages) if self.pages else "(empty)"

    def render_for_query(self, question: str) -> str:   # bounded retrieval, like GBrain
        top = _retrieve_topk(self.pages, question, self.k)
        return "\n".join(top) if top else "(empty)"

    def total_tokens(self) -> int:
        return _approx_tokens(self.render())

    def item_count(self) -> int:
        return len(self.pages)

    def snapshot(self) -> dict:
        return {"arm": self.name, "items": self.item_count(), "tokens": self.total_tokens()}


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
