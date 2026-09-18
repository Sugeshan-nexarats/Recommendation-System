

from __future__ import annotations

import logging

from app.features.abstract_feature import AbstractFeature, FeatureResult
from app.features.feature_registry import FeatureRegistry

# Import signals sub-package to trigger auto-discovery.
import app.features.quality.signals  # noqa: F401, E402

from app.features.quality.quality_config import QualityConfig
from app.features.quality.quality_signal_registry import QualitySignalRegistry
from app.models.posts import Post
from app.retrievers.user_context import UserContext

logger = logging.getLogger(__name__)

_MAX_SCORE: float = 100.0


@FeatureRegistry.register
class QualityFeature(AbstractFeature):


    def __init__(self, config: QualityConfig | None = None) -> None:
        self._config = config or QualityConfig()

    @property
    def name(self) -> str:
        return "quality_score"

    def compute(self, user: UserContext, post: Post, signal_context=None) -> FeatureResult:
        cfg = self._config
        signals = QualitySignalRegistry.all_signals()

        if not signals:
            logger.warning("QualityFeature: no signals registered; returning 0.")
            return FeatureResult(
                feature_name=self.name,
                score=0.0,
                metadata={"reason": "no_signals_registered"},
            )

        signal_results = {}
        for signal in signals:
            try:
                result = signal.compute(user, post, cfg)
                signal_results[result.signal_name] = result
            except Exception:  # noqa: BLE001
                logger.exception(
                    "QualityFeature: signal '%s' failed for post_id=%s.",
                    signal.name,
                    getattr(post, "post_id", "unknown"),
                )
                from app.features.quality.abstract_quality_signal import (
                    QualitySignalResult,
                )
                signal_results[signal.name] = QualitySignalResult(
                    signal_name=signal.name,
                    score=0.0,
                    metadata={"error": "computation_failed"},
                )

        total_weight = cfg.total_weight
        weighted_sum = 0.0
        weighted_contrib: dict[str, float] = {}

        for signal_name, result in signal_results.items():
            weight = getattr(cfg.weights, signal_name, 0.0)
            contribution = (weight / total_weight) * result.score
            weighted_sum += contribution
            weighted_contrib[signal_name] = round(contribution, 6)

        raw_score = min(max(weighted_sum * _MAX_SCORE, 0.0), _MAX_SCORE)

        logger.debug(
            "QualityFeature: post_id=%s raw_score=%.2f signals=%s",
            getattr(post, "post_id", "?"),
            raw_score,
            {k: round(v.score, 3) for k, v in signal_results.items()},
        )

        return FeatureResult(
            feature_name=self.name,
            score=round(raw_score / _MAX_SCORE, 6),
            metadata=self._build_metadata(
                raw_score, weighted_contrib, signal_results
            ),
        )

    def _build_metadata(
        self,
        raw_score: float,
        weighted_contrib: dict[str, float],
        signal_results: dict,
    ) -> dict:
        cfg = self._config

        return {
            "raw_quality_score": round(raw_score, 4),
            "signal_scores": {
                name: round(result.score, 6)
                for name, result in signal_results.items()
            },
            "weighted_contributions": weighted_contrib,
            "signal_metadata": {
                name: result.metadata
                for name, result in signal_results.items()
            },
            "active_signals": QualitySignalRegistry.signal_names(),
            "config_snapshot": {
                "weights": {
                    "content":    cfg.weights.content,
                    "spam":       cfg.weights.spam,
                    "reputation": cfg.weights.reputation,
                    "reports":    cfg.weights.reports,
                    "duplicate":  cfg.weights.duplicate,
                },
                "caps": {
                    "reports": cfg.caps.reports,
                },
            },
        }
