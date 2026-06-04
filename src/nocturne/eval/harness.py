"""The experiment harness — drives the nightly loop for every arm and both experiments.

Experiment A (brains comparison): ours (LLM consolidation) vs gbrain_accumulate vs append vs
window, over the identical 30-night stream. Per-night memory metrics + morning-QA accuracy.

Experiment B (self-improvement): ours with a self-improving policy (validation-gated hill-climb)
vs ours with a static policy. Per-night composite score -> learning curve.

Everything an arm holds is real model cognition (consolidation/REM/QA) on a simulated stream.
Results are emitted as one JSON bundle that the report and the dashboard both render from.
"""
from __future__ import annotations

from ..briefing.generator import generate_briefing
from ..hypotheses.ledger import Ledger
from ..llm import LLM
from ..memory.store import MemoryStore
from ..policy.store import PolicyStore
from ..sim.schema import WorldTrace
from ..agent import rewrite as rw
from ..agent import rem as rem_mod
from ..agent import improve as improve_mod
from ..agent.baselines import make_baseline
from ..agent.qa import answer_question
from . import metrics as M
from . import judge as J

ROLLBACK_MARGIN = 0.05


# ---------------------------------------------------------------------------
# Ours
# ---------------------------------------------------------------------------

def run_our_arm(
    llm: LLM, trace: WorldTrace, *,
    model: str | None = None,
    rem_model: str | None = None,   # heavier model for REM synthesis (falls back to `model`)
    self_improve: bool = True,
    do_rem: bool = True,
    do_briefing: bool = True,
    token_budget: int = 1200,
    half_life: float = 4.0,
    label: str | None = None,
) -> dict:
    store = MemoryStore(token_budget=token_budget)
    policy = PolicyStore.seed()
    ledger = Ledger()

    best_score = -1.0
    best_policy = policy.clone()
    nights: list[dict] = []
    qa_results: list[dict] = []
    insight_found_night: int | None = None

    for ni in trace.nights:
        n = ni.night
        policy.current_night = n
        store.advance_night(n, half_life=half_life)

        op_counts = rw.consolidate(llm, store=store, new_items=ni.items,
                                   policy_render=policy.render_for_prompt(), model=model)

        rem_props: list[str] = []
        if do_rem:
            rem_props = rem_mod.rem_synthesize(llm, store=store, ledger=ledger, night=n,
                                               model=(rem_model or model))
        if insight_found_night is None and M.insight_found(
            [h.statement for h in ledger.hypotheses], trace
        ):
            insight_found_night = n

        render = store.render_for_prompt()
        metrics = M.memory_metrics(render, len(store.items), trace, n)
        score = M.composite_score(metrics)

        # validation-gated hill-climb: keep best, roll back regressions
        if score >= best_score:
            best_score = score
            best_policy = policy.clone()
        elif self_improve and score < best_score - ROLLBACK_MARGIN:
            policy = best_policy.clone()
            policy.current_night = n

        # morning QA — ours answers from the WHOLE bounded memory (no retrieval step needed)
        for qa in trace.qa_for_night(n):
            ans = answer_question(llm, memory_render=render, question=qa.question, model=model)
            qa_results.append({"qa_id": qa.id, "night": n, "thread": qa.thread,
                               "question": qa.question, "answer": ans,
                               "correct": M.grade_qa(ans, qa),
                               "query_tokens": store.total_tokens()})

        briefing = ""
        if do_briefing:
            briefing = generate_briefing(llm, store=store, ledger=ledger, night=n, model=model)

        # self-improvement: rewrite the policy from the graded critique
        improve_counts = {}
        if self_improve:
            critique = J.build_critique(render, len(store.items), trace, n)
            improve_counts = improve_mod.improve_policy(llm, policy=policy, critique=critique,
                                                        model=model)

        nights.append({
            "night": n, "tokens": store.total_tokens(), "facts": len(store.items),
            "metrics": metrics, "score": score, "best_score": round(best_score, 4),
            "op_counts": op_counts, "improve_counts": improve_counts,
            "rem_proposed": rem_props,
            "briefing": briefing,
            "memory": store.snapshot()["items"],
            "policy": policy.snapshot()["directives"],
            "ledger": ledger.snapshot()["hypotheses"],
        })

    return {
        "arm": label or ("rewrite" if self_improve else "rewrite_static"),
        "self_improve": self_improve,
        "nights": nights,
        "qa": qa_results,
        "qa_accuracy": _qa_acc(qa_results),
        "avg_query_tokens": _avg_query_tokens(qa_results),
        "insight_found_night": insight_found_night,
        "final_policy": policy.snapshot()["directives"],
        "usage": llm.usage.snapshot(),
    }


# ---------------------------------------------------------------------------
# Baselines
# ---------------------------------------------------------------------------

def run_baseline_arm(llm: LLM, trace: WorldTrace, arm_name: str, *, model: str | None = None) -> dict:
    arm = make_baseline(arm_name)
    has_retrieval = hasattr(arm, "render_for_query")
    nights: list[dict] = []
    qa_results: list[dict] = []
    for ni in trace.nights:
        n = ni.night
        arm.ingest(n, ni.items)
        render = arm.render()  # full store → storage-footprint metrics
        metrics = M.memory_metrics(render, arm.item_count(), trace, n)
        for qa in trace.qa_for_night(n):
            # retrieval arms answer from top-K (like GBrain); naive arms dump the whole store
            qrender = arm.render_for_query(qa.question) if has_retrieval else render
            ans = answer_question(llm, memory_render=qrender, question=qa.question, model=model)
            qa_results.append({"qa_id": qa.id, "night": n, "thread": qa.thread,
                               "question": qa.question, "answer": ans,
                               "correct": M.grade_qa(ans, qa),
                               "query_tokens": _tok(qrender)})
        nights.append({"night": n, "tokens": arm.total_tokens(), "facts": arm.item_count(),
                       "metrics": metrics, "score": M.composite_score(metrics)})
    return {"arm": arm_name, "nights": nights, "qa": qa_results,
            "qa_accuracy": _qa_acc(qa_results), "avg_query_tokens": _avg_query_tokens(qa_results),
            "usage": llm.usage.snapshot()}


# ---------------------------------------------------------------------------
# Experiments
# ---------------------------------------------------------------------------

DEFAULT_ARMS = ["rewrite", "gbrain_accumulate", "append", "window"]


def experiment_brains(llm: LLM, trace: WorldTrace, *, arms: list[str] | None = None,
                      model: str | None = None, rem_model: str | None = None) -> dict:
    arms = arms or DEFAULT_ARMS
    results = {}
    for a in arms:
        if a == "rewrite":
            results[a] = run_our_arm(llm, trace, model=model, rem_model=rem_model,
                                     self_improve=True, do_rem=True, do_briefing=True,
                                     label="rewrite")
        else:
            results[a] = run_baseline_arm(llm, trace, a, model=model)
    return results


def experiment_selfimprove(llm: LLM, trace: WorldTrace, *, model: str | None = None) -> dict:
    improving = run_our_arm(llm, trace, model=model, self_improve=True, do_rem=False,
                            do_briefing=False, label="self_improving")
    static = run_our_arm(llm, trace, model=model, self_improve=False, do_rem=False,
                         do_briefing=False, label="static_policy")
    return {"self_improving": improving, "static_policy": static}


def _qa_acc(qa_results: list[dict]) -> float:
    if not qa_results:
        return 0.0
    return round(sum(1 for q in qa_results if q["correct"]) / len(qa_results), 4)


def _tok(s: str) -> int:
    return max(1, len(s) // 4)


def _avg_query_tokens(qa_results: list[dict]) -> int:
    vals = [q.get("query_tokens", 0) for q in qa_results]
    return round(sum(vals) / len(vals)) if vals else 0
