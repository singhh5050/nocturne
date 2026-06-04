# nocturne — slideshow voiceover script

Self-contained deck: `artifacts/slideshow.html` (open in a browser, full-screen, `→`/`←` or click to advance; the demo slide auto-pilots itself). Target ~5–6 min. Real numbers below come from the tiered DigitalOcean run (`gpt-oss-20b` bulk + `gpt-oss-120b` REM), 5 seeds.

Format per slide: **[SLIDE]** what's on screen — *(rubric item)* — then the words to say.

---

**[1 · TITLE]** "nocturne", the moon, the epigraph; the nebula drifting.
> "This is nocturne — a sleep-time research agent. While you sleep, it doesn't pile up everything that happened. It draws a constellation: the few things worth steering by tomorrow. Let me show you why that's the right bet — and how it beats the obvious alternative."

**[2 · THE INSPIRATION]** Cellarius epigraph; procedural constellation forming. — *(Communication / originality)*
> "The whole project is inspired by baroque star atlases — Cellarius, 1660. Here's the idea, and it's the thesis, not decoration: the night sky is an overwhelming field of stars. The astronomer working through the night doesn't catalog every one — they draw a few constellations: bounded figures you navigate by. Everything you'll see is drawn fresh in code; we borrowed the period, not its pictures."

**[3 · Q1 · PROBLEM & INSIGHT]** append/accumulate vs the inverted question. — *(Problem & Insight)*
> "Most agent memory appends — the more it runs, the bigger it gets. The most prominent system of 2026, Garry Tan's GBrain, leans all the way in: a hundred-and-forty-six-thousand-page library you retrieve from. Great answer to 'how do I never forget anything?' nocturne asks the inverted question: what's the *smallest* memory that still makes me effective tomorrow? Working memory, not a library."

**[4 · Q2 · HOW IT WORKS]** two-level diagram; sleep stages. — *(Execution / Research)*
> "One primitive — add, merge, reweight, drop — runs at two levels. Level one rewrites what I know: episodic memory. Level two rewrites *how I decide what's worth knowing*: the agent's own policy, edited each morning from a graded critique of its briefing. Overnight it runs sleep stages — consolidate, then a REM pass that looks for connections across threads. All of it is real model cognition on the live API."

**[5–6 · LIVE DEMO]** the embedded app auto-pilots. — *(Execution + the wow)*
> "This is the actual app — thirty simulated nights of a PhD student's life. Watch the memory consolidate. … Night eleven: the lab meeting moves from Thursday to Wednesday. nocturne *reconciles* — it drops the stale time and keeps the current one, and logs the decision. A never-forget library keeps both. … Night twenty-two: a paper from night six and an experiment anomaly from night thirteen — never stated together — get synthesized into a confirmed insight. … And I can click any star to see *why* the brain believes it — its provenance."

**[7 · EVALUATION & EVIDENCE]** brains table + charts + ablations. — *(Evaluation & Evidence — the big one)*
> "We tested it honestly. Four memory strategies, the identical thirty-night stream, five seeds. Ours holds about three hundred tokens; accumulation bloats past twelve thousand. Needle-survival F1: ours zero-point-six-four, accumulation zero-point-zero-two. And the comparison is fair — we give the library real top-K retrieval, so we don't strawman its query cost. The win isn't tokens; it's that ours reconciles, self-improves, and stays compact. Ablations confirm every layer earns its place: turn off REM and the insight never surfaces; turn off forgetting and noise creeps in; turn off self-improvement and quality drops."

**[8 · SELF-IMPROVEMENT]** learning curve. — *(Evidence)*
> "And it teaches itself. With a deliberately naive starting policy, the self-improving agent's score climbs to zero-point-six-seven; a frozen policy stays at zero-point-one. You can read the directives it wrote for itself — 'drop promotional mail,' 'keep deadlines and advisor follow-ups.' GBrain has no mechanism for that."

**[9 · vs SOTA]** the wins table. — *(comparison to prior work)*
> "So where do we stand against the state of the art? We're not competing with GBrain — we're the layer it's missing. It's long-term memory; we're working memory and executive function. We reconcile contradictions where it surfaces both; we push a briefing where it waits to be asked; we self-improve where it's fixed. The honest trade: it wins long-tail recall, because we forget on purpose. They're complementary — nocturne sits *on top* of a library like GBrain."

**[10 · DATA & METHODS]** disclosure. — *(Integrity)*
> "One honest note on method: the thirty-day stream is a *simulated*, ground-truth-labeled environment — we built the generator so this is reproducible and testable at a month's scale. The inputs are simulated; every bit of the reasoning is a real model running on DigitalOcean."

**[11 · Q3 · USE CASES + Q4 · ROADMAP]**
> "Who's this for? Any researcher, founder, or clinician drowning in streams who wants to wake up oriented, not buried. It's a reusable, auditable working-memory layer for any agent. Next: real source connectors, a nightly cron, and wiring nocturne on top of a bottomless library like GBrain through MCP — the two halves of memory, together."

**[12 · CLOSE]** repo + integrity.
> "Built solo, with heavy AI assistance — disclosed in the README — on real compute. Clean, reproducible, one file to open. That's nocturne: the smallest memory that still makes you effective tomorrow. Thanks."

---

### Recording checklist
- Open `artifacts/slideshow.html` full-screen; the WebGL nebula + demo need a real browser (Chrome).
- Let the demo slide breathe (~45–60s) — the auto-pilot scrubs to nights 11 and 22 and clicks a star.
- Numbers to keep straight: store ~315 vs ~12k tokens · F1 0.64 vs 0.02 · self-improve 0.67 vs 0.10 · 5 seeds.
- Keep the simulation disclosure line (slide 10) — it's cheap and it's the honest play.
