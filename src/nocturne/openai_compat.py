"""OpenAI-compatible inference engine (e.g. DigitalOcean Gradient / serverless inference).

DigitalOcean's inference endpoint speaks the OpenAI Chat Completions API, so we drive it with the
`openai` SDK pointed at a custom base_url. Same interface as nocturne.llm.LLM (complete /
complete_json) so the harness is provider-agnostic. Records cassettes for offline --replay.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from .config import Settings
from .llm import Usage, _safe_json


def _key(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:24]


class OpenAICompatLLM:
    def __init__(self, settings: Settings, *, mode: str = "live",
                 cassette_dir: str | Path = "runs/cassettes", client: Any | None = None,
                 attempts: int = 7, backoff: float = 2.0, throttle: float = 0.8,
                 temperature: float | None = None, seed: int | None = None) -> None:
        self.settings = settings
        self.mode = mode
        self.cassette_dir = Path(cassette_dir)
        self.cassette_dir.mkdir(parents=True, exist_ok=True)
        self.attempts = attempts
        self.backoff = backoff
        self.throttle = throttle  # min seconds between live calls (stay under rate limits)
        self.temperature = temperature  # vary across seeds for multi-seed variance
        self.seed = seed
        self.usage = Usage()
        self.model = settings.openai_model
        self._client = client
        if self._client is None and mode == "live":
            from openai import OpenAI
            self._client = OpenAI(base_url=settings.openai_base_url,
                                  api_key=settings.openai_api_key)

    # -- public API (mirrors llm.LLM) ----------------------------------------

    def complete(self, *, system: str, user: str, model: str | None = None,
                 max_tokens: int = 2048, effort: str = "medium", cache_system: bool = True) -> str:
        payload = self._payload(system, user, model, max_tokens, json_mode=False)
        return self._dispatch(payload)

    def complete_json(self, *, system: str, user: str, schema: dict[str, Any],
                      model: str | None = None, max_tokens: int = 2048, effort: str = "medium",
                      cache_system: bool = True) -> dict[str, Any]:
        sys2 = system + "\n\nReturn ONLY a single valid JSON object — no prose, no markdown fences."
        payload = self._payload(sys2, user, model, max_tokens, json_mode=True)
        return _safe_json(self._dispatch(payload))

    # -- internals ------------------------------------------------------------

    def _payload(self, system: str, user: str, model: str | None, max_tokens: int,
                 json_mode: bool) -> dict[str, Any]:
        # Note: we deliberately do NOT send response_format={"type":"json_object"} — on some
        # OpenAI-compatible servers (e.g. gpt-oss via DO) it corrupts the output. We rely on an
        # explicit "JSON only" instruction (added in complete_json) plus robust parsing instead.
        p = {
            "model": model or self.model,
            "max_tokens": max_tokens,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
        }
        if self.temperature is not None:
            p["temperature"] = self.temperature
        if self.seed is not None:
            p["seed"] = self.seed
        return p

    def _dispatch(self, payload: dict[str, Any]) -> str:
        key = _key(payload)
        cassette = self.cassette_dir / f"oc_{key}.json"
        if self.mode == "replay":
            if not cassette.exists():
                raise RuntimeError(f"replay cassette missing for {key}; run --do (live) once to record")
            data = json.loads(cassette.read_text())
            self.usage.add(_U(data.get("usage", {})))
            return data["text"]
        text, usage = self._call(payload)
        self.usage.add(_U(usage))
        cassette.write_text(json.dumps({"text": text, "usage": usage}, indent=2))
        return text

    def _call(self, payload: dict[str, Any]) -> tuple[str, dict]:
        last: Exception | None = None
        for i in range(self.attempts):
            try:
                resp = self._client.chat.completions.create(**payload)
                text = resp.choices[0].message.content or ""
                u = resp.usage
                usage = {"input_tokens": getattr(u, "prompt_tokens", 0) or 0,
                         "output_tokens": getattr(u, "completion_tokens", 0) or 0,
                         "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0}
                if self.throttle:
                    time.sleep(self.throttle)
                return text, usage
            except Exception as e:  # noqa: BLE001
                last = e
                msg = str(e).lower()
                # json_object unsupported on some servers -> retry without it
                if "response_format" in payload and "json" in msg:
                    payload.pop("response_format", None)
                    continue
                # some servers reject seed / temperature -> drop and retry
                if "seed" in payload and "seed" in msg:
                    payload.pop("seed", None)
                    continue
                if "temperature" in payload and "temperature" in msg:
                    payload.pop("temperature", None)
                    continue
                if i < self.attempts - 1:
                    # honor Retry-After on 429; otherwise exponential backoff (cap 45s)
                    retry_after = None
                    r = getattr(e, "response", None)
                    if r is not None:
                        try:
                            retry_after = float(r.headers.get("retry-after"))
                        except (TypeError, ValueError):
                            retry_after = None
                    rate_limited = "rate limit" in msg or "429" in msg
                    delay = retry_after if retry_after else min(45.0, self.backoff ** (i + (2 if rate_limited else 0)))
                    time.sleep(delay)
        assert last is not None
        raise last


class _U:
    def __init__(self, d: dict[str, int]) -> None:
        self.input_tokens = d.get("input_tokens", 0)
        self.output_tokens = d.get("output_tokens", 0)
        self.cache_read_input_tokens = d.get("cache_read_input_tokens", 0)
        self.cache_creation_input_tokens = d.get("cache_creation_input_tokens", 0)
