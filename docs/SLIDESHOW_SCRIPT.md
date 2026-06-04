# nocturne — voiceover script

Read verbatim while advancing the deck (`artifacts/slideshow.html`, full-screen; `→` / `←` or click;
the demo slide auto-pilots itself). ~6–8 minutes. Each block is one slide; advance at the ¶ breaks.
Numbers are the real tiered-DigitalOcean run (`gpt-oss-20b` bulk + `gpt-oss-120b` for REM), 5 seeds.

---

## Slide 1 — Title
This is **nocturne** — a sleep-time research agent. The premise is simple. You spend your day buried under papers, email, calendar invites, Slack threads — and most "memory" systems for AI just pile all of that up, forever. nocturne does the opposite. While you sleep, it sits with everything that came in and asks a harder question: *what's the smallest amount I actually need to remember to be useful to you tomorrow?* And then, crucially, it gets better at answering that question every single night. Let me show you how it works, and why I think it's a genuinely different bet from what the best systems are doing right now.

## Slide 2 — The inspiration
I want to start with where the whole idea comes from, because it's not just a coat of paint. This is inspired by the baroque star atlases — Cellarius, sixteen-sixty. Think about what a constellation actually *is*. The night sky is this overwhelming field of thousands of stars — that's the raw stream of everything happening to you. The astronomer working through the night doesn't catalog every single point of light. They draw a *constellation*: a small, deliberate figure you can actually navigate by, and pass down. That act — drawing meaning out of chaos, and choosing what to leave out — is exactly what nocturne does with your information. So everything you'll see is built in that spirit, and drawn fresh in code: the living nebula behind me, the constellations, all of it. We took the period's idea, not its pictures.

## Slide 3 — Q1: Problem & Insight
So here's the problem. Almost every agent-memory system today *appends* — the longer it runs, the bigger it gets. The most prominent one this year is GBrain, from Garry Tan at Y Combinator, and it leans all the way into that: it's a hundred-and-forty-six-thousand-page library you retrieve from. And to be clear, that's a great answer to one question — "how do I never forget anything?" But it's not the only question worth asking. nocturne asks the inverse: not "how do I keep everything," but "what's the *smallest* memory that still makes me effective tomorrow?" That's a different organ entirely. It's the difference between a library and a working memory — between a warehouse and the few notes you keep on your desk. And once you frame it that way, a bunch of capabilities fall out that a library simply doesn't have.

## Slide 4 — Q2: How it works
Mechanically, it comes down to one move, applied at two levels. The move is a small set of operations on memory — add, merge, reweight, drop. Level one is the obvious one: rewriting *what the agent knows*, consolidating the day's stream into a bounded set of notes. But level two is the interesting part — it runs that same rewrite on its *own policy*: the rules it uses to decide what's worth keeping in the first place. Every morning it grades its own briefing against what actually mattered, and edits those rules. And it all happens in stages, like sleep — a light triage pass, a deep consolidation pass, and then a REM pass that looks for connections *across* different threads. None of this is scripted; every one of those steps is a real model, reasoning live.

## Slide 5 — Live demo
Rather than tell you, let me just show you the real thing running. This is thirty nights of a PhD student's life — papers, mail, meetings, all simulated, but the agent's thinking is real. Watch the top panel: each night a flood of items comes in, and it keeps the one or two that matter and lets the rest go. … Now here's a moment I love — night eleven. The lab meeting gets moved from Thursday to Wednesday. nocturne doesn't store both times and leave you to figure it out; it *reconciles* — it drops the stale one, keeps the current truth, and logs that decision. … Down here you can see the two brains side by side: ours stays a small, legible constellation while the accumulate-everything approach just keeps exploding into a haystack. … And jump to night twenty-two — a paper from night six and an experiment result from night thirteen, which were never connected anywhere, get synthesized into an insight, and confirmed. You can click any star to see exactly which raw items the agent built it from.

## Slide 6 — Evaluation & Evidence
Now, none of that matters if it doesn't hold up, so we measured it carefully. Four memory strategies, the exact same thirty-night stream, five random seeds. The headline is right here: our agent holds about three hundred tokens of memory; the accumulate-everything approaches bloat past twelve thousand. On needle-survival F1 — did the facts that matter actually stay findable — we're at point-six-four; accumulation is at point-zero-two. And I want to be fair about this: we gave the library approach real retrieval, top-K, so we're not strawmanning its cost. The point was never to win on tokens — it's that ours stays compact, reconciles, and gets sharper. And our ablations back that up: turn off the REM stage and the insight never surfaces; turn off forgetting and noise creeps back in; turn off self-improvement and quality drops. Every piece is earning its place.

## Slide 7 — Self-improvement
That self-improvement piece deserves its own moment, because it's the part I'm proudest of. We start the agent with a deliberately naive policy — it barely knows what to keep. Over the month, the self-improving version climbs to a score of point-six-seven, while a frozen policy stays down at point-one. And the best part is you can *read* what it taught itself — directives like "drop promotional mail," "always keep deadlines and advisor follow-ups." Nobody wrote those rules; it wrote them, for itself, from its own mistakes. A fixed pipeline like GBrain has no mechanism to do that.

## Slide 8 — vs. state of the art
So where does that leave us against the state of the art? I want to be honest here: we are *not* trying to beat GBrain at being GBrain. It's a fantastic long-term memory. We're the layer it's missing. It never forgets; we forget on purpose. It surfaces both sides of a contradiction; we reconcile to the current truth. It waits for you to query it; we push you a briefing without being asked. It's a fixed pipeline; we rewrite our own. The honest trade is real — it'll beat us on recalling some arbitrary fact from six weeks ago, because we chose to let that go. Which is exactly why these are *complementary*: the natural next step is nocturne sitting on top of a library like GBrain — working memory on top of long-term memory.

## Slide 9 — Data & methods
One honest note on method, because it matters. That thirty-day stream is a *simulated*, ground-truth-labeled environment — we built the generator deliberately, so the whole system is reproducible and testable at a scale that would otherwise take a month of real data to collect. The inputs are simulated; but every bit of the actual cognition — the consolidation, the synthesis, the self-improvement — is a real model running on DigitalOcean. And the labels were written independently of the item text, so the evaluation isn't circular.

## Slide 10 — Use cases & what's next
Who is this for? Honestly, anyone drowning in streams — a researcher, a founder, a clinician — who wants to wake up oriented instead of buried. More broadly, it's a reusable, auditable working-memory layer that any agent could sit on. And what's next follows directly from everything I just said: real source connectors instead of a simulation, a nightly schedule so it actually runs while you sleep, and wiring it on top of a bottomless library like GBrain through MCP — so you get both halves of memory, working together.

## Slide 11 — Close
That's nocturne. It was built solo, with heavy AI assistance — fully disclosed in the README — on real compute. It's clean, it's reproducible, and the whole thing is one file you can open in a browser. The one idea I'd leave you with is the one we started with: the smallest memory that still makes you effective tomorrow. Thank you.

---

### Recording checklist
- Full-screen Chrome; the nebula + embedded demo need a real browser.
- On the demo slide, let the auto-pilot run (~45–60s) — it scrubs to nights 11 and 22 and clicks a star.
- Keep these numbers straight if you paraphrase: store ~300 vs ~12k tokens · F1 0.64 vs 0.02 · self-improve 0.67 vs 0.10 · 5 seeds.
- Don't drop the disclosure on slide 9 — it's the honest play and it reads as maturity.
