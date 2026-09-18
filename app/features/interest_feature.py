from __future__ import annotations
import logging
from app.features.abstract_feature import AbstractFeature, FeatureResult
from app.features.feature_registry import FeatureRegistry
from app.features.interest.abstract_similarity_computer import AbstractSimilarityComputer
from app.features.interest.jaccard_similarity_computer import JaccardSimilarityComputer
from app.features.interest.user_interest_profile import UserInterestProfile
from app.models.posts import Post
from app.retrievers.user_context import UserContext

logger = logging.getLogger(__name__)

_MAX_SCORE:          float = 100.0
_TAG_SIM_POINTS:     float = 30.0
_COMMUNITY_POINTS:   float = 20.0
_LIKED_POINTS:       float = 20.0
_WATCHED_POINTS:     float = 15.0
_SAVED_POINTS:       float = 10.0
_INTERACTED_POINTS:  float = 5.0

assert (
    _TAG_SIM_POINTS + _COMMUNITY_POINTS + _LIKED_POINTS
    + _WATCHED_POINTS + _SAVED_POINTS + _INTERACTED_POINTS
    == _MAX_SCORE
), "InterestFeature scoring rubric does not sum to 100."




@FeatureRegistry.register
class InterestFeature(AbstractFeature):


    def __init__(
        self,
        similarity_computer: AbstractSimilarityComputer | None = None,
    ) -> None:
        self._similarity = similarity_computer or JaccardSimilarityComputer()

    @property
    def name(self) -> str:
        return "interest_overlap"

    def compute(self, user: UserContext, post: Post, signal_context=None) -> FeatureResult:
   
      
        profile = UserInterestProfile.from_user_context(user)

      
        post_tags: frozenset[str] = frozenset(
            str(t).strip().lower() for t in (post.tags or []) if str(t).strip()
        )
        post_communities: frozenset[str] = frozenset(
            str(c) for c in (post.communities or [])
        )

        
        if profile.is_empty() and not post_tags:
            return FeatureResult(
                feature_name=self.name,
                score=0.0,
                metadata={
                    "raw_interest_score": 0.0,
                    "reason": "cold_start_no_signals",
                },
            )

       
        tag_sim: float = self._similarity.tag_similarity(profile, post_tags)

       
        community_sim: float = self._similarity.community_similarity(
            profile, post_communities
        )

        
        liked_match:      float = self._history_match(user.liked_tags,      post_tags)
        watched_match:    float = self._history_match(user.watched_tags,     post_tags)
        saved_match:      float = self._history_match(user.saved_tags,       post_tags)
        interacted_match: float = self._history_match(user.interacted_tags,  post_tags)

      
        raw_score: float = (
            tag_sim          * _TAG_SIM_POINTS
            + community_sim  * _COMMUNITY_POINTS
            + liked_match    * _LIKED_POINTS
            + watched_match  * _WATCHED_POINTS
            + saved_match    * _SAVED_POINTS
            + interacted_match * _INTERACTED_POINTS
        )

      
        raw_score = min(max(raw_score, 0.0), _MAX_SCORE)

        logger.debug(
            "InterestFeature: post_id=%s raw_score=%.2f (tag=%.3f comm=%.3f "
            "liked=%.3f watched=%.3f saved=%.3f interact=%.3f)",
            getattr(post, "post_id", "?"),
            raw_score,
            tag_sim, community_sim,
            liked_match, watched_match, saved_match, interacted_match,
        )

        return FeatureResult(
            feature_name=self.name,
            
            score=round(raw_score / _MAX_SCORE, 6),
            metadata={
                
                "raw_interest_score":   round(raw_score, 4),

               
                "tag_similarity":       round(tag_sim, 6),
                "community_similarity": round(community_sim, 6),
                "liked_match":          round(liked_match, 6),
                "watched_match":        round(watched_match, 6),
                "saved_match":          round(saved_match, 6),
                "interacted_match":     round(interacted_match, 6),

               
                "breakdown_pts": {
                    "tag_similarity":       round(tag_sim        * _TAG_SIM_POINTS, 4),
                    "community_similarity": round(community_sim  * _COMMUNITY_POINTS, 4),
                    "liked_match":          round(liked_match    * _LIKED_POINTS, 4),
                    "watched_match":        round(watched_match  * _WATCHED_POINTS, 4),
                    "saved_match":          round(saved_match    * _SAVED_POINTS, 4),
                    "interacted_match":     round(interacted_match * _INTERACTED_POINTS, 4),
                },

                
                "profile_top_tags":     profile.top_tags(10),
                "profile_total_weight": round(profile.total_weight(), 4),
                "profile_source_counts": profile.source_counts,
                "post_tag_count":       len(post_tags),
                "post_community_count": len(post_communities),

                "similarity_strategy":  self._similarity.name,
            },
        )

   
    @staticmethod
    def _history_match(history_tags: list[str], post_tags: frozenset[str]) -> float:
        
        if not history_tags or not post_tags:
            return 0.0

       
        history_set: frozenset[str] = frozenset(
            str(t).strip().lower() for t in history_tags if str(t).strip()
        )

        if not history_set:
            return 0.0

        matched = post_tags & history_set
        return len(matched) / len(post_tags)
