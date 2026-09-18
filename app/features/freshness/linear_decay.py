"""
LinearDecayFunction — simple, fully explainable freshness decay.

Formula:
    freshness = max(0, 1 - age_hours / half_life_hours)

Properties:
    - age=0            → freshness=1.0
    - age=half_life    → freshness=0.5  (same as exponential at half_life)
    - age=2×half_life  → freshness=0.0  (hits zero, then clamps)

When to use:
    - When explainability to non-technical stakeholders is important.
    - Platforms with more uniform content consumption patterns.
    - When you want a predictable, hard freshness horizon at 2× half_life.

Comparison to ExponentialDecay:
    Linear decays faster in the 0–half_life window and cuts to zero at
    2× half_life.  Exponential is gentler in the first few hours but
    never fully reaches zero (relies on max_age_hours gate instead).
"""

from __future__ import annotations

from app.features.freshness.abstract_decay_function import AbstractDecayFunction
from app.features.freshness.freshness_config import FreshnessConfig


class LinearDecayFunction(AbstractDecayFunction):
    """Freshness decay: straight-line decrease to zero at 2× half_life."""

    @property
    def name(self) -> str:
        return "linear"

    def apply(self, age_hours: float, config: FreshnessConfig) -> float:
        """
        Compute linear decay: 1 - age / half_life, floored at 0.

        Naturally hits 0.0 at 2× half_life_hours.
        The max_age_hours gate in FreshnessFeature applies an additional
        hard cutoff if max_age < 2× half_life.
        """
        if age_hours <= 0.0:
            return 1.0

        raw = 1.0 - (age_hours / config.half_life_hours)
        return max(0.0, raw)
