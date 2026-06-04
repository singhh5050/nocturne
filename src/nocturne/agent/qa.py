"""Answer a morning question from a given memory rendering (used by every arm)."""
from __future__ import annotations

from ..llm import LLM
from .prompts import QA_SYSTEM


def answer_question(
    llm: LLM, *, memory_render: str, question: str,
    model: str | None = None, effort: str = "low",
) -> str:
    user = f"MEMORY:\n{memory_render}\n\nQUESTION: {question}"
    return llm.complete(system=QA_SYSTEM, user=user, model=model, effort=effort,
                        max_tokens=256).strip()
