"""Multi-seed + ablation batch runner.

Runs the full experiment over K seeds (varying the model's sampling so we get genuine
variance bands, addressing the single-seed limitation) plus a set of ablations (REM off, decay
off, budget off, self-improvement off) to show each mechanism earns its place.

Designed to run unattended (e.g. on a DigitalOcean Droplet overnight): it is resumable via the
LLM cassettes, writes incrementally, and honors a wall-clock guard so it can't burn credits.
"""
from __future__ import annotations

import json
import statistics
import time
from pathlib import Path
from typing import Callable

from ..sim.schema import WorldTrace
from . import harness


def _final(res: dict) -> dict:
    last = res["nights"][-1]
    m = last["metrics"]
    return {"tokens": last["tokens"], "facts": last["facts"], "f1": m["f1"],
            "precision": m["precision"], "recall": m["recall"], "noise": m["noise_leak"],
            "qa": res["qa_accuracy"]}


def _agg(values: list[float]) -> dict:
    if not values:
        return {"mean": 0.0, "std": 0.0, "n": 0}
    return {"mean": round(statistics.mean(values), 4),
            "std": round(statistics.pstdev(values) if len(values) > 1 else 0.0, 4),
            "n": len(values)}


ABLATIONS = {
    "rem_off": dict(do_rem=False),
    "decay_off": dict(half_life=1e9),
    "budget_off": dict(token_budget=10_000_000),
    "improve_off": dict(self_improve=False),
}


def run_batch(
    make_llm: Callable[..., object],
    trace: WorldTrace,
    *,
    model: str | None,
    seeds: int = 5,
    do_ablations: bool = True,
    outdir: Path = Path("runs/batch"),
    max_minutes: float = 600.0,
) -> dict:
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()

    def time_left() -> bool:
        return (time.monotonic() - start) / 60.0 < max_minutes

    per_seed: list[dict] = []
    full_bundle = None
    for i in range(seeds):
        if not time_left():
            print(f"[batch] wall-clock guard hit before seed {i}; stopping.", flush=True)
            break
        temp = round(0.3 + 0.1 * i, 2)
        print(f"[batch] seed {i} (temperature={temp}) ...", flush=True)
        llm = make_llm(temperature=temp, seed=1000 + i)
        brains = harness.experiment_brains(llm, trace, model=model)
        selfimp = harness.experiment_selfimprove(llm, trace, model=model)
        bundle = {"engine": "do", "model": model, "seed": i, "temperature": temp,
                  "persona": trace.persona, "num_nights": trace.num_nights,
                  "brains": brains, "selfimprove": selfimp}
        (outdir / f"seed_{i}.json").write_text(json.dumps(bundle))
        if full_bundle is None:
            full_bundle = bundle
            Path("runs/run.json").write_text(json.dumps(bundle, indent=2))
        per_seed.append({
            "seed": i, "temperature": temp,
            "brains": {a: _final(r) for a, r in brains.items()},
            "selfimprove": {
                "best_final": selfimp["self_improving"]["nights"][-1]["best_score"],
                "static_final": selfimp["static_policy"]["nights"][-1]["score"],
            },
            "insight_night": brains["rewrite"].get("insight_found_night"),
            "usage": llm.usage.snapshot(),
        })
        print(f"[batch] seed {i} done: ours={per_seed[-1]['brains'].get('rewrite')}", flush=True)

    # aggregate across seeds
    arms = list(per_seed[0]["brains"].keys()) if per_seed else []
    aggregate = {}
    for a in arms:
        aggregate[a] = {k: _agg([s["brains"][a][k] for s in per_seed])
                        for k in ("tokens", "f1", "precision", "recall", "noise", "qa")}
    aggregate["selfimprove"] = {
        "best_final": _agg([s["selfimprove"]["best_final"] for s in per_seed]),
        "static_final": _agg([s["selfimprove"]["static_final"] for s in per_seed]),
    }

    ablations: dict = {}
    if do_ablations and time_left():
        for name, cfg in ABLATIONS.items():
            if not time_left():
                print(f"[batch] guard hit before ablation {name}; stopping.", flush=True)
                break
            print(f"[batch] ablation {name} {cfg} ...", flush=True)
            llm = make_llm(temperature=0.5, seed=42)
            res = harness.run_our_arm(llm, trace, model=model, do_briefing=False,
                                      label=f"abl_{name}", **cfg)
            ablations[name] = {**_final(res),
                               "insight_night": res.get("insight_found_night")}

    summary = {"model": model, "seeds_run": len(per_seed), "seeds_requested": seeds,
               "per_seed": per_seed, "aggregate": aggregate, "ablations": ablations,
               "minutes": round((time.monotonic() - start) / 60.0, 1)}
    (outdir / "summary.json").write_text(json.dumps(summary, indent=2))
    print(f"[batch] complete: {len(per_seed)} seeds, {len(ablations)} ablations, "
          f"{summary['minutes']} min", flush=True)
    return summary
