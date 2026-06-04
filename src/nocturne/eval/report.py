"""Aggregate a run bundle into console tables + a committed results.md."""
from __future__ import annotations

from pathlib import Path

_ARM_LABEL = {
    "rewrite": "rewrite (ours)",
    "gbrain_accumulate": "gbrain-style accumulate",
    "append": "naive append",
    "window": "sliding window",
}


def brains_rows(brains: dict) -> list[dict]:
    rows = []
    for arm, res in brains.items():
        last = res["nights"][-1]
        m = last["metrics"]
        rows.append({
            "arm": _ARM_LABEL.get(arm, arm),
            "tokens": last["tokens"],
            "facts": last["facts"],
            "f1": m["f1"],
            "precision": m["precision"],
            "recall": m["recall"],
            "noise_leak": m["noise_leak"],
            "qa_acc": res["qa_accuracy"],
        })
    return rows


def _table(rows: list[dict], cols: list[tuple[str, str]]) -> str:
    header = "| " + " | ".join(h for _, h in cols) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    out = [header, sep]
    for r in rows:
        out.append("| " + " | ".join(str(r[k]) for k, _ in cols) + " |")
    return "\n".join(out)


def print_summary(bundle: dict) -> None:
    print("\n=== Brains comparison (final night) ===")
    cols = [("arm", "arm"), ("tokens", "tokens"), ("facts", "facts"), ("f1", "F1"),
            ("precision", "prec"), ("recall", "rec"), ("noise_leak", "noise"), ("qa_acc", "QA acc")]
    print(_table(brains_rows(bundle["brains"]), cols))
    if "selfimprove" in bundle:
        imp = bundle["selfimprove"]["self_improving"]["nights"]
        sta = bundle["selfimprove"]["static_policy"]["nights"]
        print("\n=== Self-improvement ===")
        print(f"self-improving best-so-far: {imp[0]['best_score']:.3f} -> {imp[-1]['best_score']:.3f}")
        print(f"static policy score:        {sta[0]['score']:.3f} -> {sta[-1]['score']:.3f}")
        pol = bundle["selfimprove"]["self_improving"]["final_policy"]
        print("learned directives:")
        for d in pol:
            print(f"  - {d['content']}")
    rewrite = bundle["brains"].get("rewrite", {})
    if rewrite.get("insight_found_night"):
        print(f"\nPlanted insight surfaced on night {rewrite['insight_found_night']}.")


def write_results_md(bundle: dict, path: Path, chart_rel: str = "../artifacts") -> Path:
    rows = brains_rows(bundle["brains"])
    cols = [("arm", "arm"), ("tokens", "tokens (final)"), ("facts", "facts"),
            ("f1", "F1"), ("precision", "precision"), ("recall", "recall"),
            ("noise_leak", "noise in mem"), ("qa_acc", "QA accuracy")]
    md = ["# Nocturne — results", "",
          "_Simulated 30-night environment (see README → Data). Inputs are simulated; all nightly "
          "cognition is real model work on DigitalOcean serverless inference "
          "(tiered gpt-oss-20b + gpt-oss-120b)._", "",
          "## Brains comparison (consolidation vs accumulation)", "",
          _table(rows, cols), "",
          f"![memory size]({chart_rel}/memory_size.png)", "",
          f"![quality]({chart_rel}/brains_quality.png)", "",
          f"![qa]({chart_rel}/qa_accuracy.png)", ""]

    if "selfimprove" in bundle:
        imp = bundle["selfimprove"]["self_improving"]
        md += ["## Self-improvement (two-level rewrite)", "",
               f"Best-so-far composite score rose from "
               f"{imp['nights'][0]['best_score']:.3f} to {imp['nights'][-1]['best_score']:.3f} "
               "under a validation-gated hill-climb (best-so-far is monotonic by construction; "
               "we also plot the raw score).", "",
               f"![learning curve]({chart_rel}/learning_curve.png)", "",
               "### Directives the agent taught itself", ""]
        for d in imp["final_policy"]:
            md.append(f"- {d['content']}")
        md.append("")

    rewrite = bundle["brains"].get("rewrite", {})
    if rewrite.get("insight_found_night"):
        md += ["## Planted-insight synthesis", "",
               f"The agent surfaced the latent cross-thread insight on **night "
               f"{rewrite['insight_found_night']}** — a connection never stated in any single "
               "item. See the hypothesis ledger in the dashboard.", ""]

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(md))
    return path
