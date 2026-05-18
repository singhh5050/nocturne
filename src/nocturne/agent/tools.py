"""Tool definitions exposed to the nightly Claude agent."""
from __future__ import annotations

from typing import Callable

from ..sources.arxiv import ArxivSource
from ..sources.base import RawItem
from ..sources.calendar import CalendarSource
from ..sources.gmail import GmailSource


TOOL_SCHEMAS = [
    {
        "name": "fetch_arxiv",
        "description": "Fetch tonight's candidate papers from the researcher's arxiv subscriptions.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "fetch_gmail",
        "description": "Fetch unread/important emails since the last nightly run.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "fetch_calendar",
        "description": "Fetch tomorrow's calendar events.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]


def build_tool_handlers() -> tuple[dict[str, Callable[[], list[RawItem]]], list[RawItem]]:
    """Returns (handlers, accumulator). The accumulator collects everything fetched."""
    accumulated: list[RawItem] = []

    sources = {
        "fetch_arxiv": ArxivSource(),
        "fetch_gmail": GmailSource(),
        "fetch_calendar": CalendarSource(),
    }

    def make_handler(src):
        def _handler():
            items = src.fetch()
            accumulated.extend(items)
            return items
        return _handler

    handlers = {name: make_handler(src) for name, src in sources.items()}
    return handlers, accumulated
