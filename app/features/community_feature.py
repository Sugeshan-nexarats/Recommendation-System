from __future__ import annotations
import logging
from app.features.abstract_feature import AbstractFeature, FeatureResult
from app.features.feature_registry import FeatureRegistry
from app.models.posts import Post
from app.retrievers.user_context import UserContext

logger = logging.getLogger(__name__)

@FeatureRegistry.register
class CommunityFeature(AbstractFeature):
    
    @property
    def name(self) -> str:
        return "community_score"

    def compute(self, user: UserContext, post: Post, signal_context=None) -> FeatureResult:
        # Get unique, normalized communities from the post
        post_communities = {str(c).strip() for c in (post.communities or []) if str(c).strip()}
        
        if not post_communities:
            return FeatureResult(
                feature_name=self.name,
                score=0.0,
                metadata={
                    "reason": "no_post_communities"
                }
            )

        # Get total user affinity
        total_affinity = sum(v for v in user.community_affinity.values() if v > 0)
        
        if total_affinity == 0:
            return FeatureResult(
                feature_name=self.name,
                score=0.0,
                metadata={
                    "reason": "no_user_affinity"
                }
            )

        # Calculate matching affinity without double-counting
        matching_affinity = sum(user.community_affinity.get(c, 0.0) for c in post_communities)
        
        raw_score = matching_affinity / total_affinity
        score = min(max(raw_score, 0.0), 1.0)

        logger.debug(
            "CommunityFeature: post_id=%s matching_affinity=%.4f total_affinity=%.4f score=%.4f",
            getattr(post, "post_id", "?"),
            matching_affinity,
            total_affinity,
            score,
        )

        return FeatureResult(
            feature_name=self.name,
            score=round(score, 6),
            metadata={
                "matching_affinity": round(matching_affinity, 4),
                "total_affinity": round(total_affinity, 4),
                "post_communities": list(post_communities),
            }
        )
