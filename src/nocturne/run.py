"""nocturne CLI.

  python -m nocturne.run sim                 # (re)build + commit the 30-night trace, print stats
  python -m nocturne.run eval [--offline|--live|--replay]
  python -m nocturne.run demo --nights 12 [--offline|--live|--replay]
  python -m nocturne.run dashboard           # rebuild dashboard.html from runs/run.json

Engines:
  --offline (default): deterministic heuristic engine — zero setup, runs anywhere, for reproducibility.
  --live:              the real Anthropic model (records cassettes to runs/cassettes for replay).
  --replay:            replay committed cassettes (no API key needed; same outputs as the live run).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import get_settings
from .eval import harness, report
from .offline import OfflineLLM
from .sim.generator import build_world, load_world, save_world, stats
from .sim.schema import WorldTrace
from .viz import charts

RUN_PATH = Path("runs/run.json")
ARTIFACTS = Path("artifacts")


def make_engine(mode: str):
    settings = get_settings()
    if mode == "offline":
        return OfflineLLM(), settings
    if mode in ("do", "do-replay"):
        from .openai_compat import OpenAICompatLLM
        if mode == "do" and not settings.openai_api_key:
            print("No OPENAI_API_KEY set for the DigitalOcean endpoint; see .env.example.",
                  file=sys.stderr)
            sys.exit(2)
        return OpenAICompatLLM(settings, mode=("live" if mode == "do" else "replay"),
                               cassette_dir=settings.nocturne_cassette_dir), settings
    from .llm import LLM
    if mode == "live" and not settings.anthropic_api_key:
        print("No ANTHROPIC_API_KEY set; copy .env.example to .env.", file=sys.stderr)
        sys.exit(2)
    return LLM(settings, mode=("live" if mode == "live" else "replay"),
               cassette_dir=settings.nocturne_cassette_dir), settings


def _engine_mode(args) -> str:
    if getattr(args, "do", False):
        return "do"
    if getattr(args, "do_replay", False):
        return "do-replay"
    if args.live:
        return "live"
    if args.replay:
        return "replay"
    return "offline"


# ---------------------------------------------------------------------------

def cmd_sim(args) -> int:
    trace = build_world()
    save_world(trace)
    print(json.dumps(stats(trace), indent=2))
    print(f"\npersona: {trace.persona}")
    return 0


def _model_for(mode: str, settings) -> str | None:
    if mode in ("do", "do-replay"):
        return settings.openai_model or None
    if mode == "offline":
        return None
    return settings.nocturne_model


def _rem_model_for(mode: str, settings) -> str | None:
    # heavier model for REM cross-thread synthesis; falls back to the bulk model
    if mode in ("do", "do-replay"):
        return settings.openai_rem_model or settings.openai_model or None
    return None


def cmd_eval(args) -> int:
    mode = _engine_mode(args)
    llm, settings = make_engine(mode)
    model = _model_for(mode, settings)
    rem_model = _rem_model_for(mode, settings)
    trace = load_world()
    print(f"Running eval (engine={mode}, model={model}, rem_model={rem_model}) over "
          f"{trace.num_nights} nights x {len(harness.DEFAULT_ARMS)} arms ...", file=sys.stderr)

    brains = harness.experiment_brains(llm, trace, model=model, rem_model=rem_model)
    selfimp = harness.experiment_selfimprove(llm, trace, model=model)

    bundle = {
        "engine": mode,
        "model": model or mode,
        "rem_model": rem_model,
        "persona": trace.persona,
        "num_nights": trace.num_nights,
        "trace_stats": stats(trace),
        "brains": brains,
        "selfimprove": selfimp,
    }
    RUN_PATH.parent.mkdir(parents=True, exist_ok=True)
    RUN_PATH.write_text(json.dumps(bundle, indent=2))
    charts.render_all(bundle, ARTIFACTS)
    report.print_summary(bundle)
    report.write_results_md(bundle, Path("results.md"), chart_rel="artifacts")
    _build_dashboard(bundle)
    print(f"\nSaved bundle -> {RUN_PATH}; charts + dashboard -> {ARTIFACTS}/", file=sys.stderr)
    return 0


def cmd_demo(args) -> int:
    mode = _engine_mode(args)
    llm, settings = make_engine(mode)
    model = _model_for(mode, settings)
    full = load_world()
    n = min(args.nights, full.num_nights)
    sub = WorldTrace(
        persona=full.persona, nights=full.nights[:n],
        qa=[q for q in full.qa if q.ask_night <= n],
        needles=full.needles, insight=full.insight,
    )
    res = harness.run_our_arm(llm, sub, model=model,
                              self_improve=True, do_rem=True, do_briefing=True)
    for ni in res["nights"]:
        m = ni["metrics"]
        print(f"\n──────── night {ni['night']}  "
              f"score={ni['score']:.3f} (best {ni['best_score']:.3f})  "
              f"mem={ni['facts']} items / {ni['tokens']} tok  "
              f"F1={m['f1']:.2f} noise={m['noise_leak']}")
        print(f"  ops: {ni['op_counts']}")
        if ni["rem_proposed"]:
            print("  REM:", "; ".join(ni["rem_proposed"]))
        if ni["improve_counts"]:
            print("  policy edit:", ni["improve_counts"])
        top = ni["memory"][:3]
        if top:
            print("  top memory:")
            for it in top:
                print(f"    ({it['weight']:.2f}) {it['content'][:80]}")
    print("\nLearned policy:")
    for d in res["final_policy"]:
        print(f"  - {d['content']}")
    if res["insight_found_night"]:
        print(f"\nPlanted insight surfaced on night {res['insight_found_night']}.")
    return 0


def cmd_batch(args) -> int:
    mode = _engine_mode(args)
    settings = get_settings()
    model = _model_for(mode, settings)
    rem_model = _rem_model_for(mode, settings)
    trace = load_world()

    def make_llm(*, temperature=None, seed=None):
        if mode == "offline":
            return OfflineLLM()
        from .openai_compat import OpenAICompatLLM
        return OpenAICompatLLM(settings, mode=("live" if mode == "do" else "replay"),
                               cassette_dir=settings.nocturne_cassette_dir,
                               temperature=temperature, seed=seed)

    from .eval import batch
    summary = batch.run_batch(make_llm, trace, model=model, rem_model=rem_model, seeds=args.seeds,
                              do_ablations=not args.no_ablations, max_minutes=args.max_minutes)
    # refresh the seed-0 charts + dashboard so artifacts reflect the batch
    if RUN_PATH.exists():
        bundle = json.loads(RUN_PATH.read_text())
        charts.render_all(bundle, ARTIFACTS)
        report.write_results_md(bundle, Path("results.md"), chart_rel="artifacts")
        _build_dashboard(bundle)
    print(json.dumps(summary["aggregate"], indent=2))
    return 0


def cmd_dashboard(args) -> int:
    if not RUN_PATH.exists():
        print("No runs/run.json — run `python -m nocturne.run eval` first.", file=sys.stderr)
        return 1
    bundle = json.loads(RUN_PATH.read_text())
    _build_dashboard(bundle)
    print(f"Dashboard -> {ARTIFACTS}/dashboard.html", file=sys.stderr)
    return 0


def _build_dashboard(bundle: dict) -> None:
    from .viz import dashboard
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    dashboard.build(bundle, ARTIFACTS / "dashboard.html")


def main() -> int:
    p = argparse.ArgumentParser(prog="nocturne")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_engine_flags(sp):
        sp.add_argument("--do", action="store_true",
                        help="use the DigitalOcean OpenAI-compatible inference endpoint (real model)")
        sp.add_argument("--do-replay", dest="do_replay", action="store_true",
                        help="replay cassettes recorded from the DigitalOcean run")
        sp.add_argument("--live", action="store_true", help="use the Anthropic model")
        sp.add_argument("--replay", action="store_true", help="replay Anthropic cassettes")

    sub.add_parser("sim").set_defaults(func=cmd_sim)

    sp_eval = sub.add_parser("eval")
    add_engine_flags(sp_eval)
    sp_eval.set_defaults(func=cmd_eval)

    sp_demo = sub.add_parser("demo")
    add_engine_flags(sp_demo)
    sp_demo.add_argument("--nights", type=int, default=12)
    sp_demo.set_defaults(func=cmd_demo)

    sp_batch = sub.add_parser("batch")
    add_engine_flags(sp_batch)
    sp_batch.add_argument("--seeds", type=int, default=5)
    sp_batch.add_argument("--no-ablations", action="store_true")
    sp_batch.add_argument("--max-minutes", type=float, default=600.0)
    sp_batch.set_defaults(func=cmd_batch)

    sub.add_parser("dashboard").set_defaults(func=cmd_dashboard)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
