
from __future__ import annotations
import logging
from dataclasses import dataclass
from app.features.abstract_feature import AbstractFeature, FeatureResult
from app.features.feature_registry import FeatureRegistry
from app.features.popularity.popularity_weight_config import PopularityWeightConfig
from app.models.posts import Post
from app.retrievers.user_context import UserContext

logger = logging.getLogger(__name__)



@dataclass(frozen=True, slots=True)
class _NormalisedSignals:
    """Per-metric log-normalised values, each ∈ [0, ~1]."""

    likes:      float
    comments:   float
    shares:     float
    saves:      float
    watch_time: float



@FeatureRegistry.register
class PopularityFeature(AbstractFeature):


    def __init__(self, config: PopularityWeightConfig | None = None) -> None:
        self._config = config or PopularityWeightConfig()

    @property
    def name(self) -> str:
        return "popularity_score"

    def compute(self, user: UserContext, post: Post, signal_context=None) -> FeatureResult:  # noqa: ARG002

        cfg = self._config

       
        likes      = float(post.likes      or 0)
        comments   = float(post.comments   or 0)
        shares     = float(post.shares     or 0)
        saves      = float(post.saves      or 0)
        watch_time = float(post.watch_time or 0)

        
        norm = _NormalisedSignals(
            likes      = cfg.log_normalise(likes,      cfg.caps.likes),
            comments   = cfg.log_normalise(comments,   cfg.caps.comments),
            shares     = cfg.log_normalise(shares,     cfg.caps.shares),
            saves      = cfg.log_normalise(saves,      cfg.caps.saves),
            watch_time = cfg.log_normalise(watch_time, cfg.caps.watch_time),
        )

      
        w = cfg.weights
        raw = (
            norm.likes      * w.likes
            + norm.comments * w.comments
            + norm.shares   * w.shares
            + norm.saves    * w.saves
            + norm.watch_time * w.watch_time
        )

     
        total_weight = cfg.total_weight
        score = raw / total_weight

       
        score = min(max(score, 0.0), 1.0)

        logger.debug(
            "PopularityFeature: post_id=%s score=%.4f "
            "(likes_n=%.3f comments_n=%.3f shares_n=%.3f "
            "saves_n=%.3f wt_n=%.3f)",
            getattr(post, "post_id", "?"),
            score,
            norm.likes, norm.comments, norm.shares, norm.saves, norm.watch_time,
        )

        return FeatureResult(
            feature_name=self.name,
            score=round(score, 6),
            metadata=self._build_metadata(
                likes, comments, shares, saves, watch_time,
                norm, score, total_weight,
            ),
        )

    def _build_metadata(
        self,
        likes: float,
        comments: float,
        shares: float,
        saves: float,
        watch_time: float,
        norm: _NormalisedSignals,
        score: float,
        total_weight: float,
    ) -> dict:
       
        w   = self._config.weights
        cap = self._config.caps

        return {
          
            "raw_counts": {
                "likes":      int(likes),
                "comments":   int(comments),
                "shares":     int(shares),
                "saves":      int(saves),
                "watch_time": int(watch_time),
            },

          
            "normalised": {
                "likes":      round(norm.likes,      6),
                "comments":   round(norm.comments,   6),
                "shares":     round(norm.shares,     6),
                "saves":      round(norm.saves,      6),
                "watch_time": round(norm.watch_time, 6),
            },

           
            "weighted_contrib": {
                "likes":      round(norm.likes      * w.likes      / total_weight, 6),
                "comments":   round(norm.comments   * w.comments   / total_weight, 6),
                "shares":     round(norm.shares     * w.shares     / total_weight, 6),
                "saves":      round(norm.saves      * w.saves      / total_weight, 6),
                "watch_time": round(norm.watch_time * w.watch_time / total_weight, 6),
            },

            
            "final_score": round(score, 6),

          
            "config_snapshot": {
                "weights": {
                    "likes":      w.likes,
                    "comments":   w.comments,
                    "shares":     w.shares,
                    "saves":      w.saves,
                    "watch_time": w.watch_time,
                },
                "caps": {
                    "likes":      cap.likes,
                    "comments":   cap.comments,
                    "shares":     cap.shares,
                    "saves":      cap.saves,
                    "watch_time": cap.watch_time,
                },
            },
        }
