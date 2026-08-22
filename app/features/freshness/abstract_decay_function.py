from __future__ import annotations
from abc import ABC, abstractmethod
from app.features.freshness.freshness_config import FreshnessConfig

class AbstractDecayFunction(ABC):

    @property
    @abstractmethod
    def name(self) -> str:
       
        ...

    @abstractmethod
    def apply(self, age_hours: float, config: FreshnessConfig) -> float:
        """
        Map post age to a freshness multiplier in [0.0, 1.0].
        """
        ...
