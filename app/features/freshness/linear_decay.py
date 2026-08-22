from __future__ import annotations
from app.features.freshness.abstract_decay_function import AbstractDecayFunction
from app.features.freshness.freshness_config import FreshnessConfig


class LinearDecayFunction(AbstractDecayFunction):
    
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
