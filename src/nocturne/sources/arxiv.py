from __future__ import annotations

from .base import RawItem, Source


class ArxivSource(Source):
    name = "arxiv"

    def fetch(self) -> list[RawItem]:
        return [
            RawItem(
                source=self.name,
                title="Sleep-time Compute: Beyond Inference Scaling at Test-time",
                body="Letta/Berkeley argue that agents with idle time should precompute over their context, "
                     "rewriting memory to lower morning-task latency.",
                url="https://arxiv.org/abs/2504.13171",
                meta={"authors": ["Lin et al."], "category": "cs.AI"},
            ),
            RawItem(
                source=self.name,
                title="MemGPT: Towards LLMs as Operating Systems",
                body="Virtual context management via paging between in-context and external memory.",
                url="https://arxiv.org/abs/2310.08560",
                meta={"category": "cs.AI"},
            ),
            RawItem(
                source=self.name,
                title="Reflexion: Language Agents with Verbal Reinforcement Learning",
                body="Verbal self-reflection improves task performance across reasoning, coding, and decision-making.",
                url="https://arxiv.org/abs/2303.11366",
                meta={"category": "cs.LG"},
            ),
            RawItem(
                source=self.name,
                title="Constitutional AI for Long-Horizon Agents",
                body="Applying constitutional methods to multi-step agentic workflows.",
                url="https://arxiv.org/abs/2999.99999",
                meta={"category": "cs.AI"},
            ),
        ]
