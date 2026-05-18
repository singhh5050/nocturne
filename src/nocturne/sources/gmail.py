from __future__ import annotations

from .base import RawItem, Source


class GmailSource(Source):
    name = "gmail"

    def fetch(self) -> list[RawItem]:
        return [
            RawItem(
                source=self.name,
                title="Re: ICLR submission — reviewer 2 questions",
                body="Reviewer 2 asks for additional ablations on the rewrite-vs-append baseline. "
                     "Response due Friday.",
                meta={"from": "advisor@stanford.edu", "thread_id": "t-1"},
            ),
            RawItem(
                source=self.name,
                title="Compute grant approved",
                body="Your H100 allocation for May has been approved. Quota: 2400 GPU-hours.",
                meta={"from": "cluster-admin@cs.stanford.edu"},
            ),
            RawItem(
                source=self.name,
                title="Weekly newsletter: The Batch",
                body="Promotional content, mostly recaps you've seen.",
                meta={"from": "newsletter@deeplearning.ai", "promotional": True},
            ),
        ]
