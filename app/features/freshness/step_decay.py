from __future__ import annotations
from app.features.freshness.abstract_decay_function import AbstractDecayFunction
from app.features.freshness.freshness_config import FreshnessConfig

class StepDecayFunction(AbstractDecayFunction):
    """Freshness decay: binary 1.0 / 0.0 switch at half_life boundary."""

    @property
    def name(self) -> str:
        return "step"

    def apply(self, age_hours: float, config: FreshnessConfig) -> float:
       
        return 1.0 if age_hours <= config.half_life_hours else 0.0
