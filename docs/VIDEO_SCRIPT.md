# nocturne — demo video script (~5–6 min)

Target: under 10 min (3–6 is fine). Maps to the four required questions and the rubric. Screens to
show are in **[brackets]**. Keep the disclosure line in — it's cheap and it's the honest play.

---

## 0. Cold open (15s) — [terminal: `python -m nocturne.run demo --nights 12 --do-replay`]
"This is nocturne. While a researcher sleeps, it doesn't pile up everything that happened —
it rewrites what it knows into a small, sharp memory, and it rewrites *how it decides what to keep*.
Watch one night." (Let a night scroll: ops, top memory, a learned policy edit.)

## 1. Q1 — Why did you build this? (45s) — [README: Why section / the GBrain contrast]
- The bottleneck: agent memory mostly *appends*. The most famous 2026 system, GBrain, leans all the
  way into accumulation — 146k+ pages, a library you retrieve from.
- nocturne asks the opposite question: **what's the smallest memory that still makes me effective
  tomorrow?** Bounded working memory, active forgetting, consolidation.
- Inspired by sleep-time compute (2504.13171) + Reflexion (2303.11366).

## 2. Q2 — How does it work? (Automation / Agent Systems) (110s)
- **[README diagram]** One primitive — add/merge/reweight/drop — at **two levels**: episodic memory
  AND the agent's own policy. Show `ops.py` is literally shared by both stores.
- **[diagram]** A night: light triage → deep consolidate → REM cross-thread synthesis → morning
  briefing → judge vs ground truth → self-improve (rewrite the policy), validation-gated hill-climb.
- **[dashboard.html]** Scrub the 30 nights:
  - constellation shrinks/clusters as memory consolidates;
  - the **lab-meeting** item changes on night 11 and the old one is *reconciled away*, not duplicated;
  - the **collaboration** thread fades after it goes silent (forgetting);
  - the **policy panel** gains a directive the agent wrote for itself.

## 3. The two payoffs (60s) — [dashboard scrubber]
- **Self-improvement:** drag across nights; the learned-policy panel fills in; the learning-curve
  chart climbs vs the flat static control. "It taught itself: drop promotional mail; keep deadlines."
- **Planted insight:** stop on night 13 — an *open* hypothesis appears linking a night-6 paper to a
  night-13 anomaly (a connection never stated in any single item). Scrub to night 22 — new data lands
  and the ledger flips it to **confirmed**. That's cross-thread synthesis, not retrieval.

## 4. Q-evidence — Evaluation (75s) — [results.md table + charts]
- Four arms on the *identical* 30-night stream: rewrite (ours) vs gbrain-style accumulate vs naive
  append vs sliding window. Baselines are mechanical; every arm answers the same morning questions
  with the same model from its own memory.
- **[memory_size.png]** accumulation bloats ~20–25×; ours stays flat under a token budget.
- **[brains_quality.png / table]** ours: high needle recall, far higher precision, ~zero noise.
- **[qa_accuracy.png]** ours answers next-day questions at a fraction of the token cost — the
  sleep-time-compute payoff. Window forgets old facts.
- Failure analysis: single seed, best-so-far is monotonic by design (disclosed), decay can drop a
  premise early.

## 5. **Disclosure (10s)** — say it plainly
"One honest note: the 30-day stream is a *simulated*, ground-truth-labeled environment — we built the
generator so this is reproducible and testable at a month's scale. The inputs are simulated; every
bit of the reasoning is a real model running on DigitalOcean inference."

## 6. Q3 — Use cases & impact (35s)
- A morning briefing that stays sharp for any researcher / founder / clinician drowning in streams.
- It's a reusable *working-memory layer* for any agent — bounded, auditable (provenance), self-tuning.

## 7. Q4 — What's next (25s)
- Real OAuth sources + nightly cron on DigitalOcean; multi-seed eval with variance.
- Complementary to GBrain: nocturne as the bounded consolidation layer **on top of** GBrain's
  bottomless library (via MCP) — different halves of the same problem.

## 8. Close (10s) — [GitHub repo + dashboard]
"Clean, reproducible, one file to open. Thanks." [show repo URL]

---

### Recording checklist
- [ ] `python -m nocturne.run eval --do-replay` first so charts/dashboard reflect the committed run.
- [ ] Have `artifacts/dashboard.html` open full-screen; pre-position on nights 11, 13, 22.
- [ ] Have `results.md` and the four PNGs ready.
- [ ] Keep it tight — the dashboard scrub is the star; let it breathe for ~60s.
