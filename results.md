# Nocturne — results

_Simulated 30-night environment (see README → Data). Inputs are simulated; all nightly cognition is real model work on DigitalOcean serverless inference (tiered gpt-oss-20b + gpt-oss-120b)._

## Brains comparison (consolidation vs accumulation)

| arm | tokens (final) | facts | F1 | precision | recall | noise in mem | QA accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- |
| rewrite (ours) | 315 | 10 | 0.5714 | 0.4 | 1.0 | 0 | 0.8333 |
| gbrain-style accumulate | 11873 | 320 | 0.0247 | 0.0125 | 1.0 | 300 | 1.0 |
| naive append | 12415 | 320 | 0.0247 | 0.0125 | 1.0 | 300 | 0.8333 |
| sliding window | 1556 | 40 | 0.0909 | 0.05 | 0.5 | 40 | 0.6667 |

![memory size](artifacts/memory_size.png)

![quality](artifacts/brains_quality.png)

![qa](artifacts/qa_accuracy.png)

## Self-improvement (two-level rewrite)

Best-so-far composite score rose from 0.000 to 0.667 under a validation-gated hill-climb (best-so-far is monotonic by construction; we also plot the raw score).

![learning curve](artifacts/learning_curve.png)

### Directives the agent taught itself

- Drop promotional newsletters and unsolicited marketing emails; never store them.
- Store only facts with a clear source and timestamp; discard unverified data.
- Merge overlapping items about the same entity to avoid duplicates; keep the most comprehensive version.
- Up‑weight items containing explicit deadlines as the deadline nears, prioritizing them in memory retrieval.

## Planted-insight synthesis

The agent surfaced the latent cross-thread insight on **night 6** — a connection never stated in any single item. See the hypothesis ledger in the dashboard.
