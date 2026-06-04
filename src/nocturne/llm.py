"""Anthropic client wrapper for nocturne.

Responsibilities:
  - Retries with backoff (on top of the SDK's own retries).
  - Prompt caching on the stable system prefix (verified via usage.cache_read_input_tokens).
  - A reliable structured-JSON path using `output_config.format` (prefills are removed on
    Sonnet 4.6 / Opus 4.8, so we never prefill).
  - Record / replay "cassettes": every live call is keyed by a hash of its request and written
    to a JSON file, so the whole experiment regenerates offline (`--replay`) with no API key.
  - A mockable surface (`LLM.complete` / `LLM.complete_json`) so tests inject a fake.

Models (per the claude-api skill): claude-sonnet-4-6 for bulk, claude-opus-4-8 for judge/REM.
Adaptive thinking only; effort via output_config.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from .config import Settings


# Token accounting shared across a run (for the pareto / cost charts).
class Usage:
    def __init__(self) -> None:
        self.input_tokens = 0
        self.output_tokens = 0
        self.cache_read_input_tokens = 0
        self.cache_creation_input_tokens = 0
        self.calls = 0

    def add(self, u: Any) -> None:
        self.calls += 1
        self.input_tokens += getattr(u, "input_tokens", 0) or 0
        self.output_tokens += getattr(u, "output_tokens", 0) or 0
        self.cache_read_input_tokens += getattr(u, "cache_read_input_tokens", 0) or 0
        self.cache_creation_input_tokens += getattr(u, "cache_creation_input_tokens", 0) or 0

    def snapshot(self) -> dict[str, int]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_read_input_tokens": self.cache_read_input_tokens,
            "cache_creation_input_tokens": self.cache_creation_input_tokens,
            "calls": self.calls,
        }


def _request_key(payload: dict[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:24]


class LLM:
    """Mockable Anthropic wrapper with caching + record/replay.

    mode:
      - "live":   call the real API, record responses to the cassette dir.
      - "replay": serve responses from the cassette dir; error if a key is missing.
    """

    def __init__(
        self,
        settings: Settings,
        *,
        mode: str = "live",
        cassette_dir: str | Path = "runs/cassettes",
        client: Any | None = None,
        attempts: int = 4,
        backoff: float = 1.6,
    ) -> None:
        self.settings = settings
        self.mode = mode
        self.cassette_dir = Path(cassette_dir)
        self.cassette_dir.mkdir(parents=True, exist_ok=True)
        self.attempts = attempts
        self.backoff = backoff
        self.usage = Usage()
        self._client = client
        if self._client is None and mode == "live":
            from anthropic import Anthropic
            self._client = Anthropic(api_key=settings.anthropic_api_key)

    # -- public API -----------------------------------------------------------

    def complete(
        self,
        *,
        system: str,
        user: str,
        model: str | None = None,
        max_tokens: int = 2048,
        effort: str = "medium",
        cache_system: bool = True,
    ) -> str:
        """Plain text completion. System prefix is cached when long enough."""
        payload = self._build_payload(
            system=system, user=user, model=model, max_tokens=max_tokens,
            effort=effort, cache_system=cache_system,
        )
        resp = self._dispatch(payload)
        return _text_of(resp)

    def complete_json(
        self,
        *,
        system: str,
        user: str,
        schema: dict[str, Any],
        model: str | None = None,
        max_tokens: int = 2048,
        effort: str = "medium",
        cache_system: bool = True,
    ) -> dict[str, Any]:
        """Structured JSON via output_config.format. Returns the parsed dict.

        Falls back to brace-extraction if the response is wrapped; returns {} on hard failure
        so a single bad call never crashes a 30-night run.
        """
        payload = self._build_payload(
            system=system, user=user, model=model, max_tokens=max_tokens,
            effort=effort, cache_system=cache_system,
        )
        # merge format into output_config (keep effort)
        payload["output_config"]["format"] = {"type": "json_schema", "schema": schema}
        resp = self._dispatch(payload)
        text = _text_of(resp)
        return _safe_json(text)

    # -- internals ------------------------------------------------------------

    def _build_payload(
        self, *, system: str, user: str, model: str | None,
        max_tokens: int, effort: str, cache_system: bool,
    ) -> dict[str, Any]:
        model = model or self.settings.nocturne_model
        system_block: Any
        if cache_system:
            system_block = [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]
        else:
            system_block = system
        return {
            "model": model,
            "max_tokens": max_tokens,
            "system": system_block,
            "messages": [{"role": "user", "content": user}],
            "output_config": {"effort": effort},
        }

    def _dispatch(self, payload: dict[str, Any]) -> Any:
        key = _request_key(payload)
        cassette = self.cassette_dir / f"{key}.json"

        if self.mode == "replay":
            if not cassette.exists():
                raise RuntimeError(
                    f"replay cassette missing for request {key}; run --live once to record it"
                )
            data = json.loads(cassette.read_text())
            self.usage.add(_DictUsage(data.get("usage", {})))
            return _ReplayResponse(data["text"])

        # live
        resp = self._call_with_retries(payload)
        self.usage.add(resp.usage)
        cassette.write_text(json.dumps({
            "text": _text_of(resp),
            "usage": {
                "input_tokens": getattr(resp.usage, "input_tokens", 0),
                "output_tokens": getattr(resp.usage, "output_tokens", 0),
                "cache_read_input_tokens": getattr(resp.usage, "cache_read_input_tokens", 0),
                "cache_creation_input_tokens": getattr(resp.usage, "cache_creation_input_tokens", 0),
            },
        }, indent=2))
        return resp

    def _call_with_retries(self, payload: dict[str, Any]) -> Any:
        last: Exception | None = None
        for i in range(self.attempts):
            try:
                return self._client.messages.create(**payload)
            except Exception as e:  # noqa: BLE001 - we re-raise after backoff
                last = e
                if i < self.attempts - 1:
                    time.sleep(self.backoff ** i)
        assert last is not None
        raise last


# -- helpers ------------------------------------------------------------------

class _DictUsage:
    def __init__(self, d: dict[str, int]) -> None:
        self.input_tokens = d.get("input_tokens", 0)
        self.output_tokens = d.get("output_tokens", 0)
        self.cache_read_input_tokens = d.get("cache_read_input_tokens", 0)
        self.cache_creation_input_tokens = d.get("cache_creation_input_tokens", 0)


class _ReplayBlock:
    type = "text"
    def __init__(self, text: str) -> None:
        self.text = text


class _ReplayResponse:
    def __init__(self, text: str) -> None:
        self.content = [_ReplayBlock(text)]
        self.stop_reason = "end_turn"
        self.usage = _DictUsage({})


def _text_of(resp: Any) -> str:
    return "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")


def _safe_json(text: str) -> dict[str, Any]:
    import re
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    else:
        brace = text.find("{")
        if brace > 0:
            text = text[brace:]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}
