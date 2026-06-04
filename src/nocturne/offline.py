"""Offline heuristic engine — a deterministic stand-in for the model.

PURPOSE: zero-setup reproducibility. Course staff (or anyone without an API key) can run the full
pipeline — the eval, the charts, and the time-machine dashboard — with `--offline` and get a
working artifact. It is explicitly NOT the model: it is a transparent set of heuristics that mimics
the *shape* of the model's behavior (consolidate, reconcile, forget, synthesize, self-improve).

The headline results in the paper/README come from `--live` (the real Anthropic model). This engine
exists so the repository runs end-to-end out of the box, and so the test suite stays deterministic.
The bundle records which engine produced it (`bundle["engine"]`).
"""
from __future__ import annotations

import re

_STOP = {"the", "a", "an", "of", "to", "and", "is", "in", "on", "for", "that", "what",
         "does", "do", "did", "was", "now", "are", "your", "you", "how", "many", "when", "who"}


def _toks(s: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", s.lower()) if len(w) > 2 and w not in _STOP}


class _Usage:
    def __init__(self):
        self.calls = 0
    def snapshot(self):
        return {"input_tokens": 0, "output_tokens": 0, "cache_read_input_tokens": 0,
                "cache_creation_input_tokens": 0, "calls": self.calls}


class OfflineLLM:
    def __init__(self) -> None:
        self.usage = _Usage()

    # -- structured paths -----------------------------------------------------

    def complete_json(self, *, system, user, schema, model=None, max_tokens=2048,
                      effort="medium", cache_system=True):
        self.usage.calls += 1
        # Order matters: IMPROVE/REM prompts also mention "memory-consolidation", so route the
        # specific stages before the generic substring.
        if "REM stage" in system:
            return self._rem(user)
        if "self-improvement stage" in system:
            return self._improve(user)
        if "memory-consolidation" in system:
            return self._consolidate(user)
        return {"ops": []}

    def complete(self, *, system, user, model=None, max_tokens=2048, effort="medium",
                 cache_system=True):
        self.usage.calls += 1
        if "morning briefing" in system:
            return self._briefing(user)
        return self._qa(user)

    # -- consolidation: keep signal, drop noise, reconcile contradictions -----

    def _consolidate(self, user: str) -> dict:
        policy_text = user.split("LEARNED POLICY:")[-1].split("CURRENT MEMORY:")[0].lower()
        mem_block = user.split("CURRENT MEMORY:")[-1].split("NEW ITEMS tonight:")[0]
        new_block = user.split("NEW ITEMS tonight:")[-1]
        # Policy-driven behavior: the agent only knows to drop noise once it has taught itself
        # a directive to do so. This is what makes self-improvement a *real* mechanism offline —
        # behavior changes when the policy changes.
        drop_noise = bool(re.search(r"promotional|low-signal|newsletter|recruiter|chatter|noise",
                                    policy_text))
        # existing memory lines: "- (id, w=..) [tags] content"
        existing = []
        for line in mem_block.splitlines():
            m = re.match(r"^- \(([0-9a-f]+),", line.strip())
            if m:
                existing.append((m.group(1), line.strip()))
        ops: list[dict] = []
        # Once the agent has learned to drop noise, also clean any noise that leaked in
        # before the directive existed (residual cleanup) — active forgetting.
        if drop_noise:
            for eid, eline in existing:
                if "safe to ignore" in eline.lower():
                    ops.append({"op": "drop", "id": eid, "reason": "noise"})
        for line in new_block.splitlines():
            line = line.strip()
            m = re.match(r"^\[([^\]|]+)\|[^\]]+\]\s*(.*)$", line)
            if not m:
                continue
            rid, text = m.group(1).strip(), m.group(2)
            low = text.lower()
            if "safe to ignore" in low:
                if drop_noise:
                    continue  # learned to drop noise
                ops.append({"op": "add", "tier": "episodic", "content": text,
                            "weight": 0.3, "provenance": [rid]})  # leaks until the agent learns
                continue
            # reconcile: a time/schedule change supersedes an existing related item
            if any(k in low for k in ("moving", "move", "now ", "updated", "changed", "drop")):
                for eid, eline in existing:
                    if len(_toks(text) & _toks(eline)) >= 2:
                        ops.append({"op": "drop", "id": eid, "reason": "superseded"})
            tier = "preferences" if ("saved" in low or "interest" in low) else "in_progress"
            weight = 1.6 if any(k in low for k in ("deadline", "due", "reviewer", "advisor")) else 1.0
            ops.append({"op": "add", "tier": tier, "content": text, "weight": weight,
                        "provenance": [rid]})
        return {"ops": ops}

    # -- REM: detect the latent cross-thread insight --------------------------

    def _rem(self, user: str) -> dict:
        low = user.lower()
        has_x = "interfer" in low or "consolidat" in low
        has_y = ("drop" in low and ("grows" in low or "past ~40" in low or "in the way" in low))
        confirmed = any(k in low for k in ("bounded-memory", "recovered", "fixed it", "held flat"))
        # Propose when both premises are present (the latent link), OR confirm later when the
        # confirming evidence lands — even if the original anomaly note has since faded from memory.
        if not ((has_x and has_y) or (confirmed and has_x)):
            return {"hypotheses": []}
        conf = 0.85 if confirmed else 0.4
        return {"hypotheses": [{
            "statement": "The accuracy drop in accumulation is interference at scale; "
                         "consolidation / bounded memory fixes it — compression beats accumulation.",
            "confidence": conf,
            "support_ids": [],
            "tags": ["insight", "memory"],
        }]}

    # -- self-improvement: derive directives from the critique ----------------

    def _improve(self, user: str) -> dict:
        low = user.lower()
        ops = []
        if "noise items that leaked" in low and not re.search(r"leaked into memory: 0", low):
            ops.append({"op": "add", "content": "Drop promotional, newsletter, and recruiter items; "
                                                "never store low-signal chatter.", "weight": 1.5})
        if "missing" in low and "none" not in low.split("missing")[1][:8]:
            ops.append({"op": "add", "content": "Always retain items with deadlines, advisor "
                                                "follow-ups, and schedule changes; consolidate them "
                                                "into the existing thread.", "weight": 1.5})
        if "bloating" in low:
            ops.append({"op": "add", "content": "Consolidate same-thread items and forget resolved "
                                                "or silent threads to keep memory compact.", "weight": 1.3})
        return {"ops": ops}

    # -- QA: answer from the best-matching memory line ------------------------

    def _qa(self, user: str) -> str:
        mem = user.split("MEMORY:")[-1].split("QUESTION:")[0]
        q = user.split("QUESTION:")[-1]
        qtok = _toks(q)
        best, best_overlap = "", 0
        for line in mem.splitlines():
            line = line.strip(" -")
            ov = len(_toks(line) & qtok)
            if ov > best_overlap:
                best, best_overlap = line, ov
        return best if best_overlap >= 1 else "unknown"

    def _briefing(self, user: str) -> str:
        mem = user.split("memory (post-rewrite):")[-1].split("Hypothesis ledger:")[0]
        top = [ln.strip() for ln in mem.splitlines() if ln.strip().startswith("- ")][:4]
        body = "\n".join(top) if top else "- (nothing notable)"
        return f"# Morning briefing\n## What's open\n{body}\n"
