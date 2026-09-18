"""
StepDecayFunction — binary freshness window.

Formula:
    freshness = 1.0   if age_hours <= half_life_hours
    freshness = 0.0   otherwise

Properties:
    - All posts within the half_life window score equally fresh (1.0).
    - All posts beyond the window score floor_score (applied by caller).
    - No gradual decay between the two states.

When to use:
    - Live event feeds where content is either current or irrelevant.
    - Breaking-news feeds with a strict editorial freshness window.
    - A/B testing against smoother curves to measure impact on CTR.

Limitations:
    The hard boundary can cause abrupt ranking changes at the exact
    half_life threshold.  This is intentional — if you want a gentler
    transition, use ExponentialDecayFunction or LinearDecayFunction.
"""

from __future__ import annotations

from app.features.freshness.abstract_decay_function import AbstractDecayFunction
from app.features.freshness.freshness_config import FreshnessConfig


class StepDecayFunction(AbstractDecayFunction):
    """Freshness decay: binary 1.0 / 0.0 switch at half_life boundary."""

    @property
    def name(self) -> str:
        return "step"

    def apply(self, age_hours: float, config: FreshnessConfig) -> float:
        """
        Return 1.0 if post is within the half_life window, else 0.0.

        The max_age_hours gate and floor_score in FreshnessFeature are
        redundant for this function but still applied for consistency.
        """
        return 1.0 if age_hours <= config.half_life_hours else 0.0
