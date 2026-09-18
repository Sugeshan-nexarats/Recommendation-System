"""
ExponentialDecayFunction — smooth, rapid early decay freshness curve.

Formula:
    freshness = exp(-λ × age_hours)

    where λ = ln(2) / half_life_hours
              (so that freshness(half_life) = 0.5 exactly)

Properties:
    - age=0        → freshness=1.0   (brand-new)
    - age=half_life → freshness=0.5  (by definition)
    - age=∞        → freshness→0     (asymptotic, never zero)

    The max_age_hours gate in FreshnessFeature clamps the lower bound
    to floor_score/100 for posts older than the hard cutoff.

When to use:
    - Real-time feeds where recency is critical.
    - Platforms where content engagement drops sharply within hours.
    - News feeds, sports scores, live event content.

Tuning:
    Decrease half_life_hours → faster decay (more aggressive freshness).
    Increase half_life_hours → slower decay (favours evergreen content).
"""

from __future__ import annotations

import math

from app.features.freshness.abstract_decay_function import AbstractDecayFunction
from app.features.freshness.freshness_config import FreshnessConfig


class ExponentialDecayFunction(AbstractDecayFunction):
    """Default freshness decay: smooth exponential curve."""

    @property
    def name(self) -> str:
        return "exponential"

    def apply(self, age_hours: float, config: FreshnessConfig) -> float:
        """
        Compute exp(-λ × age_hours) where λ = ln(2) / half_life_hours.

        Returns 1.0 for age_hours=0 (brand-new post).
        Approaches 0 asymptotically for old posts.
        """
        if age_hours <= 0.0:
            return 1.0

        # Decay rate derived from half_life so freshness(half_life) = 0.5 exactly.
        # Using log(2) / half_life guarantees this property regardless of config.
        decay_rate = math.log(2.0) / config.half_life_hours
        return math.exp(-decay_rate * age_hours)
