from __future__ import annotations

from .base import RawItem, Source


class CalendarSource(Source):
    name = "calendar"

    def fetch(self) -> list[RawItem]:
        return [
            RawItem(
                source=self.name,
                title="Advisor meeting — 10:00",
                body="Weekly 1:1. Bring updates on the memory rewrite experiments.",
                meta={"when": "2026-05-17T10:00", "duration_min": 30},
            ),
            RawItem(
                source=self.name,
                title="Lab seminar — 14:00",
                body="Talk: 'Sleep-time compute in practice'. Attend.",
                meta={"when": "2026-05-17T14:00", "duration_min": 60},
            ),
        ]
