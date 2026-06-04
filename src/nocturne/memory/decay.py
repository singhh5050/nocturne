"""Ebbinghaus-style forgetting curve + reinforcement.

Memory weight decays toward zero the longer an item goes unmentioned; a fresh mention
reinforces it. This is what lets the rebuttal arc stay hot while the fizzled collaboration
fades on its own — active forgetting rather than accumulation.
"""
from __future__ import annotations

import math

# Half-life in nights: after this many unreinforced nights, weight halves.
DEFAULT_HALF_LIFE = 4.0
# Multiplicative bump applied when an item is reinforced (re-mentioned).
REINFORCE_FACTOR = 1.5
WEIGHT_CEILING = 2.5


def decayed_weight(weight: float, nights_elapsed: float, half_life: float = DEFAULT_HALF_LIFE) -> float:
    """Exponential decay: w * 0.5 ** (elapsed / half_life)."""
    if nights_elapsed <= 0:
        return weight
    return weight * math.pow(0.5, nights_elapsed / half_life)


def reinforce(weight: float, factor: float = REINFORCE_FACTOR) -> float:
    return min(WEIGHT_CEILING, weight * factor)
