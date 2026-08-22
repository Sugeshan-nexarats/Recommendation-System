"""
AbstractScoringStrategy — Strategy interface for the RankingEngine.

The Strategy pattern is applied here because there are multiple valid ways
to aggregate feature scores into a single relevance score:

    WeightedSumStrategy       — configurable weighted dot-product (default).
    BayesianAverageStrategy   — future: handles sparse feature vectors.
    LearnedModelStrategy      — future: XGBoost / LightGBM gradient-boosted trees.
    TwoTowerStrategy          — future: neural embedding similarity.

The RankingEngine accepts any AbstractScoringStrategy and delegates all
aggregation logic to it.  Swapping strategies is a one-line change at the
DI wiring layer — no engine code changes required.

Interface contract:
    score(features)     → final relevance score ∈ [0.0, 1.0]
    breakdown(features) → dict mapping feature_name → weighted contribution

Both methods are required because the RankingEngine exposes the breakdown
on every RankingResult for explainability without needing to call the
strategy twice.  Implementations are expected to share computation between
the two methods (e.g. via a shared private method).
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from app.features.abstract_feature import FeatureResult


class AbstractScoringStrategy(ABC):
    """
    Strategy interface for aggregating feature signals into a scalar score.

    All implementations MUST:
      - Return scores in [0.0, 1.0].
      - Be stateless between calls (safe for concurrent use).
      - Ignore unknown feature names gracefully (return 0 contribution)
        rather than raising.  New features may be deployed before the
        strategy configuration is updated.
      - Produce a breakdown dict whose values sum to approximately the
        returned score (within floating-point tolerance).
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Human-readable name of this strategy.

        Included in RankingResult metadata for A/B experiment attribution.
        Convention: snake_case (e.g. "weighted_sum", "learned_model_v2").
        """
        ...

    @abstractmethod
    def score(self, features: list[FeatureResult]) -> float:
        """
        Aggregate a list of feature results into a single relevance score.

        Args:
            features: Feature results for a single (user, post) pair.
                      May be empty (returns 0.0).

        Returns:
            A relevance score in [0.0, 1.0].  Higher is more relevant.
        """
        ...

    @abstractmethod
    def breakdown(self, features: list[FeatureResult]) -> dict[str, float]:
        """
        Return each feature's individual weighted contribution to the score.

        The values in the returned dict should sum to approximately the value
        returned by ``score(features)`` for the same input.

        Args:
            features: Same feature results as passed to ``score()``.

        Returns:
            Mapping of feature_name → weighted contribution (≥ 0.0).
            Features not present in the strategy's weight map are omitted.
        """
        ...
