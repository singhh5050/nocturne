"""Claude tool-use loop with retries and a mockable client wrapper."""
from __future__ import annotations

import time
from typing import Any, Callable, Protocol

from .prompts import NIGHTLY_SYSTEM
from .tools import TOOL_SCHEMAS, build_tool_handlers
from ..sources.base import RawItem


class ClaudeClient(Protocol):
    def messages_create(self, **kwargs: Any) -> Any: ...


class AnthropicClientWrapper:
    """Thin wrapper around anthropic.Anthropic so we can swap in a fake for tests."""

    def __init__(self, api_key: str):
        from anthropic import Anthropic
        self._client = Anthropic(api_key=api_key)

    def messages_create(self, **kwargs: Any) -> Any:
        return self._client.messages.create(**kwargs)


def _call_with_retries(fn: Callable[[], Any], *, attempts: int = 3, backoff: float = 1.5) -> Any:
    last_exc: Exception | None = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as e:
            last_exc = e
            if i < attempts - 1:
                time.sleep(backoff ** i)
    assert last_exc is not None
    raise last_exc


def run_nightly_loop(
    client: ClaudeClient,
    *,
    model: str,
    max_iters: int = 8,
) -> tuple[str, list[RawItem]]:
    """Run the tool-use loop. Returns (final_text, accumulated_raw_items)."""
    handlers, accumulated = build_tool_handlers()

    messages: list[dict[str, Any]] = [
        {"role": "user", "content": "Run the nightly cycle. Fetch from all sources, then summarize the new signals."}
    ]

    final_text = ""
    for _ in range(max_iters):
        resp = _call_with_retries(
            lambda: client.messages_create(
                model=model,
                max_tokens=2048,
                system=NIGHTLY_SYSTEM,
                tools=TOOL_SCHEMAS,
                messages=messages,
            )
        )

        messages.append({"role": "assistant", "content": resp.content})

        tool_uses = [b for b in resp.content if getattr(b, "type", None) == "tool_use"]
        text_blocks = [b for b in resp.content if getattr(b, "type", None) == "text"]

        if text_blocks:
            final_text = "\n".join(b.text for b in text_blocks)

        if getattr(resp, "stop_reason", None) != "tool_use" or not tool_uses:
            break

        tool_results = []
        for tu in tool_uses:
            handler = handlers.get(tu.name)
            if handler is None:
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tu.id,
                    "content": f"error: unknown tool {tu.name}",
                    "is_error": True,
                })
                continue
            items = handler()
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tu.id,
                "content": "\n".join(f"- {it.title}: {it.body}" for it in items),
            })

        messages.append({"role": "user", "content": tool_results})

    return final_text, accumulated
