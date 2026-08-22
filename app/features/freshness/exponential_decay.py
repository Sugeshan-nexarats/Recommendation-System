from __future__ import annotations
import math
from app.features.freshness.abstract_decay_function import AbstractDecayFunction
from app.features.freshness.freshness_config import FreshnessConfig


class ExponentialDecayFunction(AbstractDecayFunction):

    @property
    def name(self) -> str:
        return "exponential"

    def apply(self, age_hours: float, config: FreshnessConfig) -> float:
        """
        Compute exp(-λ × age_hours) where λ = ln(2) / half_life_hours.
        """
        if age_hours <= 0.0:
            return 1.0

        decay_rate = math.log(2.0) / config.half_life_hours
        return math.exp(-decay_rate * age_hours)
