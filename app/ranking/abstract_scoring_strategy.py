from __future__ import annotations
from abc import ABC, abstractmethod
from app.features.abstract_feature import FeatureResult


class AbstractScoringStrategy(ABC):
    

    @property
    @abstractmethod
    def name(self) -> str:

        ...

    @abstractmethod
    def score(self, features: list[FeatureResult]) -> float:
   
        ...

    @abstractmethod
    def breakdown(self, features: list[FeatureResult]) -> dict[str, float]:

        ...
