

from __future__ import annotations

from app.features.abstract_feature import FeatureResult
from app.ranking.abstract_scoring_strategy import AbstractScoringStrategy
from app.ranking.weight_config import FeatureWeightConfig


class WeightedSumStrategy(AbstractScoringStrategy):


    def __init__(self, config: FeatureWeightConfig | None = None) -> None:
        self._config = config or FeatureWeightConfig()

    @property
    def name(self) -> str:
        return "weighted_sum"

    def score(self, features: list[FeatureResult]) -> float:

        return round(sum(self._breakdown_values(features).values()), 6)

    def breakdown(self, features: list[FeatureResult]) -> dict[str, float]:
 
        return {
            name: round(contribution, 6)
            for name, contribution in self._breakdown_values(features).items()
            if contribution > 0.0
        }

    def _breakdown_values(
        self, features: list[FeatureResult]
    ) -> dict[str, float]:
 
        result: dict[str, float] = {}
        for fr in features:
            weight = self._config.weight_for(fr.feature_name)
            result[fr.feature_name] = weight * fr.score
        return result
