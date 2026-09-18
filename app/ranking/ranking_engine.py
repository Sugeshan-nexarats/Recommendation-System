

from __future__ import annotations

import logging

from app.ranking.abstract_scoring_strategy import AbstractScoringStrategy
from app.ranking.ranking_input import RankingInput
from app.ranking.ranking_result import RankingResult

logger = logging.getLogger(__name__)


class RankingEngine:


    def __init__(self, strategy: AbstractScoringStrategy) -> None:
        self._strategy = strategy


    def rank(self, inputs: list[RankingInput]) -> list[RankingResult]:

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
