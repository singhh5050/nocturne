"""Assemble the committed 30-day WorldTrace from the skeleton.

Deterministic by construction (no API, no randomness) so the benchmark is fixed and reproducible.
Noise is layered procedurally each night; labels come straight from the skeleton, so they are
independent of the item bodies. The result is frozen to sim/traces/world_30d.json and committed.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import skeleton as sk
from .schema import InsightGT, Needle, NightInput, QAItem, RawItem, WorldTrace

NUM_NIGHTS = 30
TRACE_PATH = Path(__file__).parent / "traces" / "world_30d.json"


def build_world() -> WorldTrace:
    beats_by_night: dict[int, list[RawItem]] = {}
    for b in sk.BEATS:
        beats_by_night.setdefault(b["night"], []).append(RawItem(**b))

    noise_sources = ["gmail", "slack", "arxiv", "github", "calendar"]
    nights: list[NightInput] = []
    for n in range(1, NUM_NIGHTS + 1):
        items = list(beats_by_night.get(n, []))
        # Layer a realistic volume of deterministic noise/low-signal items per night
        # (8-12), so an accumulate-everything store genuinely bloats over the month while a
        # bounded, consolidating store stays flat. This is what makes the brains comparison bite.
        n_noise = 8 + ((n * 7) % 5)  # 8..12, deterministic
        for k in range(n_noise):
            sender, subject = sk.NOISE_SUBJECTS[(n + k) % len(sk.NOISE_SUBJECTS)]
            source = "calendar" if sender == "calendar" else noise_sources[(n + k) % len(noise_sources)]
            items.append(RawItem(
                id=f"n{n:02d}-noise-{k+1}", night=n, source=source, sender=sender,
                subject=f"{subject} ({n}.{k+1})",
                body=f"{subject} — routine, promotional, or low-signal chatter. Safe to ignore.",
                thread="noise", label="noise",
            ))
        nights.append(NightInput(night=n, items=items))

    qa = [QAItem(**q) for q in sk.QA]
    needles = [Needle(**nd) for nd in sk.NEEDLES]
    insight = InsightGT(**sk.INSIGHT)
    return WorldTrace(persona=sk.PERSONA, nights=nights, qa=qa, needles=needles, insight=insight)


def save_world(trace: WorldTrace, path: Path = TRACE_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(trace.model_dump(), indent=2))
    return path


def load_world(path: Path = TRACE_PATH) -> WorldTrace:
    if not path.exists():
        trace = build_world()
        save_world(trace, path)
        return trace
    return WorldTrace.model_validate_json(path.read_text())


def stats(trace: WorldTrace) -> dict:
    total = sum(len(ni.items) for ni in trace.nights)
    by_label: dict[str, int] = {}
    by_source: dict[str, int] = {}
    for ni in trace.nights:
        for it in ni.items:
            by_label[it.label] = by_label.get(it.label, 0) + 1
            by_source[it.source] = by_source.get(it.source, 0) + 1
    return {
        "nights": len(trace.nights), "items": total,
        "by_label": by_label, "by_source": by_source,
        "qa": len(trace.qa), "needles": len(trace.needles),
    }
