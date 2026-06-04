"""End-to-end smoke + unit tests with a deterministic FakeLLM (no API)."""
from __future__ import annotations

import re

import pytest

from nocturne.eval import harness
from nocturne.eval import metrics as M
from nocturne.memory.store import MemoryStore
from nocturne.ops import apply_ops, parse_ops
from nocturne.policy.store import PolicyStore
from nocturne.sim.generator import build_world


# ---- a deterministic stand-in for the Anthropic client ----------------------

class FakeLLM:
    """Implements the LLM surface (complete / complete_json) with no network.

    Consolidation: keep every non-noise new item, drop anything labelled 'safe to ignore'.
    This makes the 'ours' arm bounded and noise-free, which is enough to exercise the harness.
    """
    def __init__(self) -> None:
        class _U:  # usage stub
            def snapshot(self):
                return {"input_tokens": 0, "output_tokens": 0,
                        "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0, "calls": 0}
        self.usage = _U()

    def complete_json(self, *, system, user, schema, model=None, max_tokens=2048,
                      effort="medium", cache_system=True):
        if "REM stage" in system:
            return {"hypotheses": []}
        if "self-improvement stage" in system:
            return {"ops": [{"op": "add", "content": "Drop promotional newsletters.", "weight": 1.4}]}
        if "memory-consolidation" in system:
            ops = []
            block = user.split("NEW ITEMS tonight:")[-1]
            for line in block.splitlines():
                line = line.strip()
                m = re.match(r"^\[([^\]|]+)\|[^\]]+\]\s*(.*)$", line)
                if not m:
                    continue
                text = m.group(2)
                if "safe to ignore" in text.lower():
                    continue  # drop noise
                ops.append({"op": "add", "tier": "in_progress", "content": text,
                            "weight": 1.0, "provenance": [m.group(1).strip()]})
            return {"ops": ops}
        return {"ops": []}

    def complete(self, *, system, user, model=None, max_tokens=2048, effort="medium",
                 cache_system=True):
        if "morning briefing" in system:
            return "# Morning briefing\n- (test) open items\n"
        return "unknown"


# ---- unit tests -------------------------------------------------------------

def test_ops_apply_and_budget():
    store = MemoryStore(token_budget=8)
    env = parse_ops({"ops": [
        {"op": "add", "tier": "in_progress", "content": "low value filler text that is long", "weight": 0.2},
        {"op": "add", "tier": "episodic", "content": "h100 grant 2400 gpu-hours", "weight": 1.9},
    ]})
    counts = apply_ops(store, env)
    assert counts["add"] == 2
    store.enforce_budget()
    remaining = [i.content for i in store.ranked()]
    assert any("2400" in c for c in remaining)            # high-weight needle kept
    assert not any("filler" in c for c in remaining)       # low-weight filler evicted


def test_parse_skips_bad_ops():
    env = parse_ops({"ops": [{"op": "bogus"}, {"op": "drop", "id": "x"}]})
    assert len(env.ops) == 1


def test_policy_uses_same_primitive():
    p = PolicyStore.seed()
    apply_ops(p, parse_ops({"ops": [{"op": "add", "content": "merge advisor follow-ups", "weight": 1.5}]}))
    assert any("advisor" in d.content for d in p.ranked())


# ---- end-to-end -------------------------------------------------------------

@pytest.fixture(scope="module")
def trace():
    return build_world()


def test_brains_comparison_ours_beats_accumulation(trace):
    llm = FakeLLM()
    results = harness.experiment_brains(llm, trace, arms=["rewrite", "append", "gbrain_accumulate"])

    ours_last = results["rewrite"]["nights"][-1]
    append_last = results["append"]["nights"][-1]

    # Consolidation stays compact; accumulation bloats.
    assert ours_last["tokens"] < append_last["tokens"]
    assert ours_last["facts"] < append_last["facts"]

    # Noise leaks into accumulation but not into ours.
    assert ours_last["metrics"]["noise_leak"] == 0
    assert append_last["metrics"]["noise_leak"] > 0

    # Ours retains the needles (high recall) and is far more precise.
    assert ours_last["metrics"]["recall"] >= 0.75
    assert ours_last["metrics"]["precision"] > append_last["metrics"]["precision"]


def test_selfimprove_curve_is_monotonic(trace):
    llm = FakeLLM()
    out = harness.experiment_selfimprove(llm, trace)
    best = [n["best_score"] for n in out["self_improving"]["nights"]]
    assert best == sorted(best)  # best-so-far never regresses (validation-gated hill-climb)
    # the agent taught itself at least one directive beyond the seed (improve step actually fires)
    assert len(out["self_improving"]["final_policy"]) >= 2
