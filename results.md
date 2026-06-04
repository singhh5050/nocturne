# Nocturne — results

_Simulated 30-night environment (see README → Data). Inputs are simulated; all nightly cognition is real model work via the Anthropic API._

## Brains comparison (consolidation vs accumulation)

| arm | tokens (final) | facts | F1 | precision | recall | noise in mem | QA accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- |
| rewrite (ours) | 485 | 15 | 0.4211 | 0.2667 | 1.0 | 0 | 0.8333 |
| gbrain-style accumulate | 11873 | 320 | 0.0247 | 0.0125 | 1.0 | 300 | 0.3333 |
| naive append | 12415 | 320 | 0.0247 | 0.0125 | 1.0 | 300 | 0.3333 |
| sliding window | 1556 | 40 | 0.0909 | 0.05 | 0.5 | 40 | 0.6667 |

![memory size](artifacts/memory_size.png)

![quality](artifacts/brains_quality.png)

![qa](artifacts/qa_accuracy.png)

## Self-improvement (two-level rewrite)

Best-so-far composite score rose from -0.200 to 0.500 under a validation-gated hill-climb (best-so-far is monotonic by construction; we also plot the raw score).

![learning curve](artifacts/learning_curve.png)

### Directives the agent taught itself

- Drop promotional, newsletter, and recruiter items; never store low-signal chatter.
- You are new here and have not yet learned what matters to this researcher; when unsure, keep the item.

## Planted-insight synthesis

The agent surfaced the latent cross-thread insight on **night 13** — a connection never stated in any single item. See the hypothesis ledger in the dashboard.
