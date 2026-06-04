"""Objective, ground-truth scorers (no LLM, no API).

These are computed against the simulation's labels, which were authored independently of the item
bodies — so the evaluation is non-circular.

Definitions (memory quality on a single night, for any arm):
  - recall    = active needles present in memory / active needles            (did the right facts survive?)
  - precision = active needles present in memory / facts held in memory      (how much of what you hold matters?)
  - f1        = harmonic mean
  - noise_leak = count of noise items sitting in memory                      (false positives)
Precision rewards a compact memory of just-the-needles and penalizes an accumulate-everything
library — which is exactly the consolidation-vs-accumulation thesis.
"""
from __future__ import annotations

from ..sim.schema import Needle, QAItem, WorldTrace


def _needle_present(text_lower: str, needle: Needle) -> bool:
    hits = sum(1 for kw in needle.keywords if kw.lower() in text_lower)
    return hits / max(1, len(needle.keywords)) >= 0.5


def active_needles(trace: WorldTrace, night: int) -> list[Needle]:
    return [nd for nd in trace.needles if nd.present_from_night <= night]


def memory_metrics(render_text: str, num_facts: int, trace: WorldTrace, night: int) -> dict:
    text = render_text.lower()
    active = active_needles(trace, night)
    matched = [nd for nd in active if _needle_present(text, nd)]
    recall = len(matched) / max(1, len(active))
    precision = len(matched) / max(1, num_facts)
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    noise_leak = text.count("safe to ignore")
    return {
        "recall": round(recall, 4),
        "precision": round(precision, 4),
        "f1": round(f1, 4),
        "needles_active": len(active),
        "needles_matched": len(matched),
        "matched_threads": sorted(nd.thread for nd in matched),
        "noise_leak": noise_leak,
        "facts": num_facts,
    }


def grade_qa(answer: str, qa: QAItem) -> bool:
    ans = answer.lower()
    if not qa.keywords:
        return False
    return all(kw.lower() in ans for kw in qa.keywords)


def insight_found(ledger_statements: list[str], trace: WorldTrace) -> bool:
    """Did the agent surface the planted cross-thread insight (by keyword overlap)?"""
    kws = [k.lower() for k in trace.insight.keywords]
    for s in ledger_statements:
        sl = s.lower()
        if sum(1 for k in kws if k in sl) >= 2:
            return True
    return False


def composite_score(m: dict) -> float:
    """A single scalar reward for the self-improvement loop: F1 minus a noise penalty."""
    return round(m["f1"] - 0.02 * m["noise_leak"], 4)
