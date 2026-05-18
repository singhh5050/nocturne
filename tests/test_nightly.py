"""Smoke test: full nightly pipeline with a fake Anthropic client."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import pytest

from nocturne.agent.loop import run_nightly_loop
from nocturne.agent.rewrite import (
    AddOp,
    DropOp,
    OpsEnvelope,
    ReweightOp,
    apply_ops,
    parse_ops,
    rewrite_memory,
)
from nocturne.briefing.generator import generate_briefing
from nocturne.memory.store import MemoryStore


@dataclass
class FakeBlock:
    type: str
    text: str = ""
    name: str = ""
    id: str = ""
    input: dict = None


@dataclass
class FakeResponse:
    content: list
    stop_reason: str = "end_turn"


class FakeClient:
    """Scriptable fake of the Anthropic client. Returns canned responses in order."""

    def __init__(self, responses: list[FakeResponse]):
        self._responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def messages_create(self, **kwargs):
        self.calls.append(kwargs)
        if not self._responses:
            raise RuntimeError("FakeClient ran out of canned responses")
        return self._responses.pop(0)


def test_parse_ops_handles_plain_json():
    raw = json.dumps({
        "ops": [
            {"op": "add", "tier": "in_progress", "content": "thing", "weight": 1.2, "tags": ["x"]},
            {"op": "drop", "id": "abc12345"},
        ]
    })
    env = parse_ops(raw)
    assert len(env.ops) == 2
    assert isinstance(env.ops[0], AddOp)
    assert isinstance(env.ops[1], DropOp)


def test_parse_ops_strips_markdown_fences():
    raw = "```json\n" + json.dumps({"ops": [{"op": "drop", "id": "x"}]}) + "\n```"
    env = parse_ops(raw)
    assert len(env.ops) == 1


def test_apply_ops_mutates_store():
    store = MemoryStore()
    stale = store.add("episodic", "old thing", weight=1.0)
    boring = store.add("in_progress", "low value thread", weight=0.5)

    env = OpsEnvelope(ops=[
        AddOp(op="add", tier="in_progress", content="reviewer 2 ablations due Friday", weight=1.8, tags=["iclr"]),
        ReweightOp(op="reweight", id=boring.id, weight=0.1),
        DropOp(op="drop", id=stale.id),
    ])

    counts = apply_ops(store, env)
    assert counts["add"] == 1
    assert counts["reweight"] == 1
    assert counts["drop"] == 1

    assert store.get(stale.id) is None
    assert store.get(boring.id).weight == pytest.approx(0.1)
    in_prog = store.by_tier("in_progress")
    assert any("reviewer 2" in i.content for i in in_prog)


def test_full_nightly_cycle_with_fake_client():
    """End-to-end: tool-use loop, then rewrite, then briefing — all with a scripted fake client."""
    # Nightly loop: turn 1 calls all three tools, turn 2 finishes with text.
    turn1_content = [
        FakeBlock(type="tool_use", name="fetch_arxiv", id="tu_1", input={}),
        FakeBlock(type="tool_use", name="fetch_gmail", id="tu_2", input={}),
        FakeBlock(type="tool_use", name="fetch_calendar", id="tu_3", input={}),
    ]
    turn2_content = [
        FakeBlock(type="text", text="Three useful signals tonight: ICLR reviewer follow-up, compute grant, advisor 1:1.")
    ]

    rewrite_json = json.dumps({
        "ops": [
            {"op": "add", "tier": "in_progress",
             "content": "ICLR reviewer 2 wants rewrite-vs-append ablations by Friday",
             "weight": 1.8, "tags": ["iclr", "deadline"]},
            {"op": "add", "tier": "episodic",
             "content": "H100 May allocation approved (2400 GPU-hours)",
             "weight": 1.0, "tags": ["compute"]},
            {"op": "add", "tier": "in_progress",
             "content": "Advisor 1:1 at 10:00 — bring memory rewrite results",
             "weight": 1.4, "tags": ["meeting"]},
        ]
    })
    turn3_content = [FakeBlock(type="text", text=rewrite_json)]

    client = FakeClient([
        FakeResponse(content=turn1_content, stop_reason="tool_use"),
        FakeResponse(content=turn2_content, stop_reason="end_turn"),
        FakeResponse(content=turn3_content, stop_reason="end_turn"),
    ])

    # 1) Run the nightly tool-use loop.
    reasoning, new_items = run_nightly_loop(client, model="fake-model", max_iters=4)
    assert "Three useful signals" in reasoning
    assert len(new_items) >= 7  # arxiv 4 + gmail 3 + calendar 2

    # 2) Run the memory rewrite.
    store = MemoryStore()
    pre_existing_count = len(store.items)
    envelope, counts = rewrite_memory(
        client,
        model="fake-model",
        store=store,
        new_items=new_items,
        nightly_reasoning=reasoning,
    )

    assert counts["add"] == 3
    assert len(store.items) == pre_existing_count + 3

    in_progress = store.by_tier("in_progress")
    assert in_progress, "expected at least one in_progress item after rewrite"
    # Highest-weight item should be the ICLR deadline.
    assert "ICLR" in in_progress[0].content or "reviewer" in in_progress[0].content.lower()

    # 3) Briefing should reflect the new state.
    briefing = generate_briefing(store)
    assert "Morning briefing" in briefing
    assert "ICLR" in briefing or "reviewer" in briefing.lower()


def test_rewrite_handles_malformed_json_gracefully():
    client = FakeClient([
        FakeResponse(content=[FakeBlock(type="text", text="sorry, I can't comply")], stop_reason="end_turn"),
    ])
    store = MemoryStore()
    store.add("in_progress", "untouched", weight=1.0)

    envelope, counts = rewrite_memory(
        client, model="fake-model", store=store, new_items=[], nightly_reasoning=""
    )

    assert envelope.ops == []
    assert counts["add"] == 0
    assert len(store.items) == 1  # nothing dropped, nothing added
