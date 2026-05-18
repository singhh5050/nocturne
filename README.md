# nocturne

A sleep-time compute agent that runs overnight to produce a morning briefing for a researcher.

## Thesis

While you sleep, an agent has hours of wall-clock time and no latency budget. It can re-read its own memory, fetch fresh signals (arxiv, mail, calendar), and *rewrite* what it knows about you — not just append. By morning, you wake to a focused briefing instead of an inbox.

The interesting primitive here is the **memory rewrite**. Most agent "memory" systems append. Nocturne instead emits structured ops — `add`, `merge`, `reweight`, `drop` — over a typed memory store. The store stays small, opinionated, and shaped by what actually matters to you, not by what arrived most recently.

See [Letta / Berkeley, "Sleep-time Compute" (arxiv:2504.13171)](https://arxiv.org/abs/2504.13171) for the broader argument.

## Quickstart

```bash
uv venv
uv pip install -e ".[dev]"
cp .env.example .env  # add your ANTHROPIC_API_KEY
python -m nocturne.run
```

Tests:

```bash
pytest
```

## Layout

- `agent/rewrite.py` — the centerpiece. Takes current memory + new raw items, asks Claude for structured JSON ops, applies them.
- `agent/loop.py` — tool-use loop with retries and a mockable client.
- `memory/store.py` — three-tier store: in-progress / episodic / preferences.
- `sources/` — stubbed connectors (arxiv, gmail, calendar). Return plausible fake items.
- `briefing/generator.py` — turns post-rewrite memory state into morning markdown.

## Roadmap

- Real OAuth source integrations (Gmail, Google Calendar, Slack, Linear)
- Learned relevance ranker trained from user accept/reject feedback on briefing items
- Proactive draft generation (reply drafts, calendar holds, paper notes)
- Planted-needle eval harness for memory rewrite quality
- Self-improvement loop: the agent revises its own prompts based on next-morning feedback
