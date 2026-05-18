"""CLI entry point: run one full nightly cycle."""
from __future__ import annotations

import sys

from .agent.loop import AnthropicClientWrapper, run_nightly_loop
from .agent.rewrite import rewrite_memory
from .briefing.generator import generate_briefing
from .config import get_settings
from .memory.store import MemoryStore


def main() -> int:
    settings = get_settings()
    if not settings.anthropic_api_key:
        print("ANTHROPIC_API_KEY not set. Copy .env.example to .env and fill it in.", file=sys.stderr)
        return 1

    client = AnthropicClientWrapper(api_key=settings.anthropic_api_key)
    store = MemoryStore.load(settings.nocturne_memory_path)

    reasoning, new_items = run_nightly_loop(
        client,
        model=settings.nocturne_model,
        max_iters=settings.nocturne_max_tool_iters,
    )

    envelope, counts = rewrite_memory(
        client,
        model=settings.nocturne_model,
        store=store,
        new_items=new_items,
        nightly_reasoning=reasoning,
    )

    store.save(settings.nocturne_memory_path)

    print(f"# Memory ops applied: {counts}", file=sys.stderr)
    print(generate_briefing(store))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
