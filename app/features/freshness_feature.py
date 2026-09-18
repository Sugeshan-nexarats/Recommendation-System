
from __future__ import annotations

import logging

from app.features.abstract_feature import AbstractFeature, FeatureResult
from app.features.feature_registry import FeatureRegistry
from app.features.freshness.abstract_age_provider import AbstractAgeProvider
from app.features.freshness.abstract_decay_function import AbstractDecayFunction
from app.features.freshness.exponential_decay import ExponentialDecayFunction
from app.features.freshness.freshness_config import FreshnessConfig
from app.features.freshness.watch_time_age_provider import WatchTimeAgeProvider
from app.models.posts import Post
from app.retrievers.user_context import UserContext

logger = logging.getLogger(__name__)

# Maximum raw score on the 0-100 rubric.
_MAX_SCORE: float = 100.0


@FeatureRegistry.register
class FreshnessFeature(AbstractFeature):
    
    def __init__(
        self,
        config:         FreshnessConfig          | None = None,
        decay_function: AbstractDecayFunction    | None = None,
        age_provider:   AbstractAgeProvider      | None = None,
    ) -> None:
        self._config         = config         or FreshnessConfig()
        self._decay_function = decay_function or ExponentialDecayFunction()
        self._age_provider   = age_provider   or WatchTimeAgeProvider()


    @property
    def name(self) -> str:
        return "freshness_score"

    def compute(self, user: UserContext, post: Post, signal_context=None) -> FeatureResult:  # noqa: ARG002
       
        cfg = self._config

        age_hours: float = self._age_provider.age_hours(post)

        # Sentinel returned by provider when age is indeterminate.
        if age_hours == float("inf"):
            return self._stale_result(
                age_hours=age_hours,
                reason="age_indeterminate",
            )

        if age_hours >= cfg.max_age_hours:
            return self._stale_result(age_hours=age_hours, reason="max_age_exceeded")

        
        multiplier: float = self._decay_function.apply(age_hours, cfg)

        
        raw_score: float = cfg.floor_score + (_MAX_SCORE - cfg.floor_score) * multiplier

      
        raw_score = min(max(raw_score, cfg.floor_score), _MAX_SCORE)

        logger.debug(
            "FreshnessFeature: post_id=%s age_hours=%.2f multiplier=%.4f "
            "raw_score=%.2f decay=%s provider=%s",
            getattr(post, "post_id", "?"),
            age_hours,
            multiplier,
            raw_score,
            self._decay_function.name,
            self._age_provider.name,
        )

        return FeatureResult(
            feature_name=self.name,
            score=round(raw_score / _MAX_SCORE, 6),
            metadata=self._build_metadata(
                age_hours=age_hours,
                multiplier=multiplier,
                raw_score=raw_score,
                stale=False,
                reason=None,
            ),
        )


    def _stale_result(self, age_hours: float, reason: str) -> FeatureResult:
        """Return a floor-score result for posts that are gated as stale."""
        floor = self._config.floor_score
        return FeatureResult(
            feature_name=self.name,
            score=round(floor / _MAX_SCORE, 6),
            metadata=self._build_metadata(
                age_hours=age_hours,
                multiplier=0.0,
                raw_score=floor,
                stale=True,
                reason=reason,
            ),
        )

    def _build_metadata(
        self,
        age_hours: float,
        multiplier: float,
        raw_score: float,
        stale: bool,
        reason: str | None,
    ) -> dict:
        """
        Build the observability metadata dict.

        Sections:
          freshness_score   — the 0-100 raw score (human-readable)
          age               — estimated age diagnostics
          decay             — decay function name, multiplier, config used
          provider          — age provider name and proxy flag
          config_snapshot   — active config values for A/B audit
        """
        cfg = self._config
        meta: dict = {
            #0-100 raw score 
            "raw_freshness_score": round(raw_score, 4),

            #Age diagnostics 
            "age_hours":round(age_hours, 4) if age_hours != float("inf") else None,
            "stale":stale,

            #Decay diagnostics 
            "decay_multiplier":  round(multiplier, 6),
            "decay_function":    self._decay_function.name,

            # Age provider attribution 
            "age_provider":      self._age_provider.name,
            "proxy_mode":        self._age_provider.is_proxy,

            # Config snapshot (for A/B audit) 
            "config_snapshot": {
                "half_life_hours": cfg.half_life_hours,
                "max_age_hours":   cfg.max_age_hours,
                "floor_score":     cfg.floor_score,
            },
        }

        if reason is not None:
            meta["reason"] = reason

        return meta
