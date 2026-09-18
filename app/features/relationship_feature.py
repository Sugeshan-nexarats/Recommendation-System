from __future__ import annotations
import logging
from app.features.abstract_feature import AbstractFeature, FeatureResult
from app.features.feature_registry import FeatureRegistry
import app.features.relationship.signals  # noqa: F401, E402

from app.features.relationship.relationship_config import RelationshipConfig
from app.features.relationship.relationship_signal_registry import RelationshipSignalRegistry
from app.models.posts import Post
from app.retrievers.user_context import UserContext

logger = logging.getLogger(__name__)

_MAX_SCORE: float = 100.0


@FeatureRegistry.register
class RelationshipFeature(AbstractFeature):
  
    def __init__(self, config: RelationshipConfig | None = None) -> None:
        self._config = config or RelationshipConfig()


    @property
    def name(self) -> str:
        return "relationship_score"

    def compute(self, user: UserContext, post: Post, signal_context=None) -> FeatureResult:

        cfg     = self._config
        signals = RelationshipSignalRegistry.all_signals()

        if not signals:
            logger.warning("RelationshipFeature: no signals registered; returning 0.")
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
                    "RelationshipFeature: signal '%s' raised an unexpected "
                    "exception for post_id=%s. Using score=0.0.",
                    signal.name,
                    getattr(post, "post_id", "unknown"),
                )
                from app.features.relationship.abstract_relationship_signal import (
                    RelationshipSignalResult,
                )
                signal_results[signal.name] = RelationshipSignalResult(
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
            "RelationshipFeature: post_id=%s raw_score=%.2f signals=%s",
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
           
            "raw_relationship_score": round(raw_score, 4),

            
            "signal_scores": {
                name: round(result.score, 6)
                for name, result in signal_results.items()
            },

           
            "weighted_contributions": weighted_contrib,

            
            "signal_metadata": {
                name: result.metadata
                for name, result in signal_results.items()
            },

            
            "active_signals": RelationshipSignalRegistry.signal_names(),

           
            "config_snapshot": {
                "weights": {
                    "creator_relationship": cfg.weights.creator_relationship,
                    "friendship":           cfg.weights.friendship,
                    "following":            cfg.weights.following,
                    "community":            cfg.weights.community,
                    "mutual_friends":       cfg.weights.mutual_friends,
                    "past_interaction":     cfg.weights.past_interaction,
                },
                "caps": {
                    "friends":      cfg.caps.friends,
                    "mutual":       cfg.caps.mutual,
                    "interactions": cfg.caps.interactions,
                },
                "creator_scores": {
                    "friend":    cfg.creator_scores.friend_score,
                    "following": cfg.creator_scores.following_score,
                    "default":   cfg.creator_scores.default_score,
                },
            },
        }
