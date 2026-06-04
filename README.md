# nocturne

**A self-improving, sleep-time research agent that rewrites what it knows *and* how it thinks — overnight — and gets measurably better at being you each night.**

> Two-level sleep-time compute: the same structured-rewrite primitive (`add` / `merge` / `reweight` / `drop`) runs on **episodic memory** (what I know) *and* on the agent's **own operating policy** (how I decide what's worth knowing).

---

## TL;DR

While you sleep, nocturne pulls your day's signals (papers, mail, calendar, Slack, GitHub, notes), and instead of *appending* everything to an ever-growing store, it **consolidates** a small, bounded working memory: merging evidence, reconciling contradictions, forgetting what's resolved, and surfacing latent cross-thread insights. Each morning it grades its own briefing against what actually mattered and **rewrites its own policy** so tomorrow's consolidation is sharper.

The central question: **does aggressive forgetting beat accumulation for a bounded working set?** We test it head-to-head against the philosophy of 2026's most prominent agent-memory system (GBrain) and find that consolidation wins on compactness, precision, and answer-cost — while retaining the facts that matter.

This is a CS 153 final project ("The One-Person Frontier Lab").

---

## Why (problem & insight)

Most agent "memory" appends. The more it runs, the bigger it gets — a library you retrieve from. **GBrain** (Garry Tan / YC, open-sourced Apr 2026; a markdown-first, self-wiring knowledge graph enriched "while you sleep") is the flagship of that bet: its production instance holds 146k+ pages. That's a great answer to *"how do I never forget anything?"*

nocturne asks the inverted question: **"what is the *smallest* memory that still makes me effective tomorrow?"** — bounded working memory under a hard token budget, with active forgetting (`drop` + Ebbinghaus decay) and LLM-driven consolidation. Library vs. working memory. Accumulation vs. compression. Those are real, opposite architectural bets, and nocturne is a small, legible instrument for studying the trade-off.

It builds on two ideas: **sleep-time compute** (spend idle compute pre-digesting context to make next-day queries cheaper/better — Lin et al., arXiv:2504.13171) and **verbal self-correction** (Reflexion, arXiv:2303.11366). The novel move is applying the *same rewrite primitive at two levels* and showing a clean result.

---

## How it works

### The primitive, at two levels

```
            ┌──────────────────────────────────────────────────────────┐
            │            structured rewrite ops                         │
            │      add · merge · reweight · drop  (src/nocturne/ops.py) │
            └───────────────┬───────────────────────┬──────────────────┘
                            │                        │
                  Level 1: memory            Level 2: policy
              (what I know)              (how I decide what to keep)
              MemoryStore                PolicyStore
              bounded · decays           directives the agent
              · provenance · budget      writes for its future self
```

`ops.py` is shared by both `MemoryStore` and `PolicyStore` — "one primitive, two levels" is literally true in the code, not a metaphor.

### A night, end to end

```
 sources ─▶ LIGHT (triage) ─▶ DEEP (consolidate: merge/reweight/drop) ─▶ REM (cross-thread synthesis)
                                        │                                      │
                                  bounded memory                       hypothesis ledger
                                        │                                      │
 morning ─▶ proactive briefing  ◀───────┴──────────────────────────────────────┘
        ─▶ judge vs ground truth ─▶ critique ─▶ SELF-IMPROVE (rewrite the policy)
                                                   validation-gated hill-climb (keep-best + rollback)
```

Key mechanisms (all in `src/nocturne/`): **provenance** (every memory item links to the raw items that produced it), a **hard token budget** that forces real tradeoffs, **Ebbinghaus decay + reinforcement**, **conflict reconciliation**, a confidence-scored **hypothesis ledger** (REM promotes an insight only when confirming evidence arrives), and **proactive briefings** (drafts + nudges).

---

## Data (methods note — please read)

The 30-day stream is a **simulated environment**, not a real inbox. We built a story-shaped, **ground-truth-labeled** life-stream generator (`src/nocturne/sim/`) so the system is reproducible and testable at a scale that would take a month to collect live. The labels (which item is a needle, which thread it belongs to, which is noise) are authored from the skeleton script **independently of the item bodies**, which keeps the evaluation non-circular.

**The inputs are simulated; the cognition is real.** Every consolidation, reconciliation, REM synthesis, self-improvement edit, and QA answer is produced by a real model via the DigitalOcean inference API — all arms see the identical stream, so results turn on real reasoning, not authored endings. The trace is frozen at `src/nocturne/sim/traces/world_30d.json`.

The trace encodes deliberate shapes: a rebuttal spine (stays hot), a collaboration that fizzles (must fade), a lab-meeting time that changes (must reconcile), a recurring paper-saving habit (must be inferred as a preference), pure noise (must be ignored), and a **planted latent insight** (a paper on night 6 + an experiment anomaly on night 13 → a synthesis the agent should surface, confirmed by new data on night 22).

---

## Results

Run on **DigitalOcean serverless inference** (`openai-gpt-oss-120b`) over the 30-night trace. Full numbers + charts regenerate into [`results.md`](results.md) and [`artifacts/`](artifacts/). Headline comparison (final night):

> _Note: the artifacts committed on `main` are regenerated with the reproducible `--offline` engine so the repo renders out of the box. The real DigitalOcean multi-seed results (with variance bands + ablations) are produced by an unattended overnight batch and land on the `overnight-results` branch (`runs/batch/summary.json`)._

> See [`results.md`](results.md) for the exact committed table from the live run. The shape of the result:
>
> - **rewrite (ours)** — tiny memory (hundreds of tokens), high needle-survival **recall**, far higher **precision**, ~zero noise, strong morning-QA accuracy.
> - **gbrain-style accumulate** / **naive append** — memory bloats ~20–25× larger, hundreds of noise items retained, precision collapses.
> - **sliding window** — compact but *forgets* old needles (low recall on early facts).

Charts (committed to `artifacts/`):

![memory size](artifacts/memory_size.png)
![needle-survival F1](artifacts/brains_quality.png)
![self-improvement](artifacts/learning_curve.png)
![morning-QA accuracy](artifacts/qa_accuracy.png)

**Self-improvement** — the self-improving policy's best-so-far score climbs over the month while a static policy stays flat; the agent's *learned directives* are legible (e.g. "drop promotional/recruiter chatter," "retain deadline + advisor items," "consolidate same-thread items"). **Planted insight** — surfaced as an open hypothesis on night 13 and **confirmed** when the night-22 evidence lands.

### The time-machine dashboard

`artifacts/dashboard.html` is a **single self-contained file** (no server, no network) — scrub all 30 nights and watch the memory **constellation**, the morning briefing, the hypothesis ledger (open → confirmed), the self-rewritten policy, and the eval charts evolve. Open it directly in a browser.

---

## Quickstart

```bash
uv venv && source .venv/bin/activate          # or: python3.11+ -m venv .venv
uv pip install -e ".[dev]"                     # or: pip install -e ".[dev]"

# zero-setup: replay the committed live run (no key needed) -> charts + dashboard
python -m nocturne.run eval --do-replay
open artifacts/dashboard.html

# run it for real on DigitalOcean inference (OpenAI-compatible)
cp .env.example .env                           # set OPENAI_BASE_URL / OPENAI_API_KEY / OPENAI_MODEL
python -m nocturne.run eval --do

# watch a few nights unfold in the terminal
python -m nocturne.run demo --nights 12 --do-replay

pytest -q                                       # deterministic test suite (no network)
```

Engines: `--do` (real DigitalOcean model, records cassettes) · `--do-replay` (replay committed cassettes, no key) · `--offline` (transparent heuristic engine for environments with no key — explicitly *not* the model; see Limitations).

---

## Repository layout

```
src/nocturne/
  ops.py            shared rewrite primitive (add/merge/reweight/drop) — used by both stores
  memory/           MemoryStore (provenance, token budget, conflict) + decay.py (Ebbinghaus)
  policy/           PolicyStore — the self-rewritten operating policy
  agent/            prompts, rewrite (deep consolidate), rem, improve, qa, baselines
  hypotheses/       confidence-scored insight ledger
  sim/              the simulation environment + frozen world_30d.json (DATA)
  eval/             metrics, judge, harness (both experiments), report
  viz/              matplotlib charts + the self-contained dashboard
  openai_compat.py  DigitalOcean (OpenAI-compatible) engine
  llm.py            Anthropic engine (optional) + caching + record/replay
  run.py            CLI: sim | eval | demo | dashboard
tests/              deterministic FakeLLM end-to-end + unit tests
artifacts/          committed charts + dashboard.html
runs/               committed run bundle + cassettes (for --do-replay)
docs/VIDEO_SCRIPT.md
```

## Evaluation methodology

Two experiments, both on the fixed labeled trace:
1. **Brains comparison** — rewrite (ours) vs gbrain-style accumulate vs naive append vs sliding window. Metrics: needle-survival precision/recall/F1, memory tokens, noise leakage, morning-QA accuracy. Baselines are *mechanical* (no LLM) so the contrast is precisely "LLM consolidation vs. mechanical accumulation"; every arm answers the same questions with the same model from its own memory.
2. **Self-improvement** — self-improving policy vs static policy; composite score over nights, with a validation-gated hill-climb (best-so-far is monotonic by construction; we also report raw score and the static control).

## Limitations & failure analysis

- **Single seed / one trace.** Results are on one labeled scenario; we do not yet report variance across seeds. (Roadmap.)
- **Best-so-far framing.** The self-improvement headline curve is monotonic by design (validation-gating). We disclose this and also plot the noisy raw score and a static-policy control.
- **Simulated inputs.** The stream is synthetic (disclosed above); the cognition is real, but real inboxes are messier than a story-shaped trace.
- **Offline engine ≠ model.** `--offline` is a transparent heuristic stand-in for zero-setup reproducibility and deterministic tests; the reported results come from `--do` (a real model). The bundle records which engine produced it.
- **Decay can drop a premise early.** A premise of the planted insight can fade from memory before the payoff; the ledger handles this by confirming on the later evidence, but a more aggressive budget can lose needles (visible in the window arm).

## AI usage disclosure

This project was built with heavy AI assistance (Anthropic's Claude, via Claude Code), used for: scaffolding the package, writing the consolidation/REM/self-improvement prompts and the harness, building the dashboard, and drafting this README. All design decisions, the experiment design, and the integrity framing were directed by the author. The runtime system itself calls a model (DigitalOcean `openai-gpt-oss-120b`) for all nightly cognition. The simulated dataset is disclosed in **Data** above. Sources are cited below.

## Citations & acknowledgements

- Lin et al., *Sleep-time Compute: Beyond Inference Scaling at Test-time* — arXiv:2504.13171 (Letta / Berkeley).
- Shinn et al., *Reflexion: Language Agents with Verbal Reinforcement Learning* — arXiv:2303.11366.
- Packer et al., *MemGPT: Towards LLMs as Operating Systems* — arXiv:2310.08560.
- **GBrain** (Garry Tan / YC), open-source agent memory — github.com/garrytan/gbrain — used as the named accumulation foil in our evaluation (design philosophy only; we do not repeat its contested benchmark numbers).
- Compute: **DigitalOcean Gradient serverless inference** (OpenAI-compatible).

## Roadmap

- Real OAuth source integrations (Gmail, Calendar, Slack, Linear) — run on real signals.
- Multi-seed eval with variance bars; a planted-needle adversarial-forgetting stress test.
- Learned relevance ranker from user accept/reject feedback on briefing items.
- Proactive drafts that send (with confirmation); deploy nightly via cron on DigitalOcean.
- **Complementary to GBrain:** nocturne as a bounded **working-memory / consolidation layer** on top of GBrain's bottomless **library** (via MCP) — they solve different halves of the problem.
