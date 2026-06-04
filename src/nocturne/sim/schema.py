"""Types for the simulated 30-day life-stream environment.

DATA DISCLOSURE: this is a *simulated* trace — a compressed, ground-truth-labeled environment
so the system is reproducible and testable at a scale that would take a month to collect live.
The labels (which item matters, which thread it belongs to, which is noise) are authored from the
skeleton script *independently* of the item bodies, which keeps evaluation non-circular.
The inputs are simulated; all nightly cognition runs on the real model.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Label = Literal["needle", "context", "noise"]


class RawItem(BaseModel):
    id: str
    night: int
    source: str            # arxiv | gmail | calendar | slack | github | notes
    sender: str
    subject: str
    body: str
    thread: str            # ground-truth thread key (e.g. "iclr_rebuttal")
    label: Label           # ground-truth importance label


class NightInput(BaseModel):
    night: int
    items: list[RawItem] = Field(default_factory=list)


class QAItem(BaseModel):
    """A 'next-morning' question with a ground-truth short answer, answerable from the stream
    up to ask_night. Used to measure whether pre-digested memory yields correct answers."""
    id: str
    ask_night: int
    question: str
    answer: str
    keywords: list[str] = Field(default_factory=list)  # acceptable-answer keywords for grading
    thread: str = ""


class Needle(BaseModel):
    """A fact/thread that MUST survive in memory at/after present_from_night."""
    id: str
    thread: str
    description: str
    present_from_night: int
    keywords: list[str]    # match against memory item content for survival scoring


class InsightGT(BaseModel):
    """Ground truth for the planted latent insight (the REM synthesis jaw-dropper).
    The connection between premises is never stated in any single item."""
    premise_item_ids: list[str]
    statement: str
    keywords: list[str]
    proposable_from_night: int   # both premises are present by here (REM could synthesize)
    confirmed_by_night: int      # confirming evidence arrives here


class WorldTrace(BaseModel):
    persona: str
    nights: list[NightInput]
    qa: list[QAItem]
    needles: list[Needle]
    insight: InsightGT

    def night(self, n: int) -> NightInput:
        for ni in self.nights:
            if ni.night == n:
                return ni
        return NightInput(night=n, items=[])

    def qa_for_night(self, n: int) -> list[QAItem]:
        return [q for q in self.qa if q.ask_night == n]

    @property
    def num_nights(self) -> int:
        return len(self.nights)
