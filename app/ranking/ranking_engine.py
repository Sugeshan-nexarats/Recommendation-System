"""
RankingEngine — Stage 4 of the recommendation pipeline.

Responsibility:
    Given a list of RankingInputs (each carrying a Post and its feature
    vector), apply a scoring strategy to every input, sort descending by
    score, assign 1-indexed ranks, and return the ordered list of
    RankingResults.

What the RankingEngine does NOT know:
    - How features are computed (FeatureRegistry / AbstractFeature).
    - How candidates were retrieved (CandidateGenerator / AbstractRetriever).
    - How results are serialised (FeedResponse / RankedPost schemas).
    - Which HTTP framework is in use.

This strict isolation means the RankingEngine can be unit-tested with
synthetic RankingInputs and a mock or real scoring strategy, with zero
infrastructure dependencies.

Strategy Pattern usage:
    The AbstractScoringStrategy is injected at construction time.
    Swapping from WeightedSumStrategy to a future LearnedModelStrategy
    is a single-line change in the DI wiring layer.
"""

from __future__ import annotations

import logging

from app.ranking.abstract_scoring_strategy import AbstractScoringStrategy
from app.ranking.ranking_input import RankingInput
from app.ranking.ranking_result import RankingResult

logger = logging.getLogger(__name__)


class RankingEngine:
    """
    Applies a scoring strategy to a pool of candidates and returns ranked
    results with full explainability metadata.

    Constructor args:
        strategy: Any AbstractScoringStrategy implementation.  Injected so
                  the engine can be tested with a mock or alternative strategy
                  without modifying this class.
    """

    def __init__(self, strategy: AbstractScoringStrategy) -> None:
        self._strategy = strategy

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def rank(self, inputs: list[RankingInput]) -> list[RankingResult]:
        """
        Score, sort, and rank a list of candidate posts.

        The engine applies the injected strategy to each input independently,
        then sorts all results by score (descending) and assigns sequential
        1-indexed rank values.

        Args:
            inputs: Candidate posts with pre-computed feature vectors.
                    May be empty — returns an empty list immediately.

        Returns:
            Sorted list of RankingResult objects, rank=1 being the most
            relevant.  The length equals len(inputs).
        """
        if not inputs:
            logger.debug("RankingEngine: received empty input list; returning []")
            return []

        logger.debug(
            "RankingEngine: scoring %d candidates with strategy='%s'",
            len(inputs),
            self._strategy.name,
        )

        # Score every candidate independently.
        scored: list[tuple[RankingInput, float, dict[str, float]]] = [
            (
                ranking_input,
                self._strategy.score(ranking_input.feature_results),
                self._strategy.breakdown(ranking_input.feature_results),
            )
            for ranking_input in inputs
        ]

        # Sort by score descending.  Python's sort is stable, so ties
        # preserve the original candidate order (retrieval order acts as
        # the tiebreaker, which favours fresher / more socially proximate
        # posts from the CandidateGenerator).
        scored.sort(key=lambda t: t[1], reverse=True)

        # Assign 1-indexed ranks and build results.
        results: list[RankingResult] = [
            RankingResult(
                post=ranking_input.post,
                rank=rank,
                score=score,
                feature_breakdown=breakdown,
            )
            for rank, (ranking_input, score, breakdown) in enumerate(scored, start=1)
        ]

        logger.debug(
            "RankingEngine: top-3 scores: %s",
            [r.score for r in results[:3]],
        )

        return results

    @property
    def strategy_name(self) -> str:
        """Expose the active strategy name for logging and observability."""
        return self._strategy.name
