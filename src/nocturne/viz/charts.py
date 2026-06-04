"""Matplotlib charts rendered from a run bundle (committed to artifacts/ for the video)."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# nocturne palette — matches the dashboard's night-observatory theme
BG = "#0b0d1c"
FG = "#edeaf7"
GRID = "#20233f"
COLORS = {
    "rewrite": "#f4b860",            # moonlight amber — ours
    "gbrain_accumulate": "#7fa8ff",  # blue — the named foil
    "append": "#e88aa8",             # rose
    "window": "#79e0d6",             # cyan
    "self_improving": "#f4b860",
    "static_policy": "#9aa0c6",
}
LABELS = {
    "rewrite": "rewrite (ours)",
    "gbrain_accumulate": "gbrain-style accumulate",
    "append": "naive append",
    "window": "sliding window",
    "self_improving": "self-improving policy (ours)",
    "static_policy": "static policy",
}


def _style(ax, title, xlabel, ylabel):
    ax.set_facecolor(BG)
    ax.set_title(title, color=FG, fontsize=11.5, pad=12, fontweight="bold")
    ax.set_xlabel(xlabel, color=FG, fontsize=10)
    ax.set_ylabel(ylabel, color=FG, fontsize=10)
    ax.tick_params(colors=FG, labelsize=9)
    for s in ax.spines.values():
        s.set_color(GRID)
    ax.grid(True, color=GRID, linewidth=0.6, alpha=0.6)


def _fig():
    fig, ax = plt.subplots(figsize=(8, 4.6), dpi=130)
    fig.patch.set_facecolor(BG)
    return fig, ax


def _save(fig, ax, path: Path):
    leg = ax.legend(facecolor=BG, edgecolor=GRID, labelcolor=FG, fontsize=9)
    if leg:
        leg.get_frame().set_alpha(0.9)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, facecolor=BG)
    plt.close(fig)


def memory_size(brains: dict, outdir: Path) -> Path:
    fig, ax = _fig()
    for arm, res in brains.items():
        ns = [n["night"] for n in res["nights"]]
        toks = [n["tokens"] for n in res["nights"]]
        ax.plot(ns, toks, color=COLORS.get(arm, FG), label=LABELS.get(arm, arm), linewidth=2.2)
    _style(ax, "Memory footprint over 30 nights — accumulation bloats, ours stays flat",
           "night", "memory size (tokens)")
    p = outdir / "memory_size.png"
    _save(fig, ax, p)
    return p


def quality(brains: dict, outdir: Path) -> Path:
    fig, ax = _fig()
    for arm, res in brains.items():
        ns = [n["night"] for n in res["nights"]]
        f1 = [n["metrics"]["f1"] for n in res["nights"]]
        ax.plot(ns, f1, color=COLORS.get(arm, FG), label=LABELS.get(arm, arm), linewidth=2.2)
    _style(ax, "Needle-survival F1 over 30 nights (higher is better)",
           "night", "F1 (precision x recall of needles)")
    p = outdir / "brains_quality.png"
    _save(fig, ax, p)
    return p


def learning_curve(selfimp: dict, outdir: Path) -> Path:
    fig, ax = _fig()
    imp = selfimp["self_improving"]["nights"]
    sta = selfimp["static_policy"]["nights"]
    ns = [n["night"] for n in imp]
    ax.plot(ns, [n["best_score"] for n in imp], color=COLORS["self_improving"],
            label=LABELS["self_improving"] + " (best-so-far)", linewidth=2.4)
    ax.plot(ns, [n["score"] for n in imp], color=COLORS["self_improving"],
            linewidth=1.0, alpha=0.4, label="self-improving (raw)")
    ax.plot([n["night"] for n in sta], [n["score"] for n in sta], color=COLORS["static_policy"],
            label=LABELS["static_policy"], linewidth=2.0, linestyle="--")
    _style(ax, "Self-improvement: best-so-far vs a static policy",
           "night", "composite score (F1 - noise penalty)")
    p = outdir / "learning_curve.png"
    _save(fig, ax, p)
    return p


def qa_bars(brains: dict, outdir: Path) -> Path:
    fig, ax = _fig()
    arms = list(brains.keys())
    accs = [brains[a]["qa_accuracy"] for a in arms]
    ax.bar([LABELS.get(a, a) for a in arms], accs,
           color=[COLORS.get(a, FG) for a in arms])
    _style(ax, "Morning-QA accuracy by arm", "arm", "accuracy")
    ax.set_ylim(0, 1)
    fig.tight_layout()
    p = outdir / "qa_accuracy.png"
    p.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(p, facecolor=BG)
    plt.close(fig)
    return p


def render_all(bundle: dict, outdir: Path) -> list[Path]:
    outdir = Path(outdir)
    paths = []
    if "brains" in bundle:
        paths += [memory_size(bundle["brains"], outdir),
                  quality(bundle["brains"], outdir),
                  qa_bars(bundle["brains"], outdir)]
    if "selfimprove" in bundle:
        paths.append(learning_curve(bundle["selfimprove"], outdir))
    return paths
