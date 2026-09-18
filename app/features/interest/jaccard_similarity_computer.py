
from __future__ import annotations
from app.features.interest.abstract_similarity_computer import AbstractSimilarityComputer
from app.features.interest.user_interest_profile import UserInterestProfile


class JaccardSimilarityComputer(AbstractSimilarityComputer):


    @property
    def name(self) -> str:
        return "weighted_jaccard"


    def tag_similarity(
        self,
        profile: UserInterestProfile,
        post_tags: frozenset[str],
    ) -> float:
        """Weighted Jaccard similarity between user profile tags and post tags."""
        if not post_tags or not profile.tag_weights:
            return 0.0

       
        all_tags = set(profile.tag_weights.keys()) | post_tags

        weighted_intersection = 0.0
        weighted_union = 0.0

        for tag in all_tags:
            w_profile = profile.tag_weights.get(tag, 0.0)
            w_post    = 1.0 if tag in post_tags else 0.0

            weighted_intersection += min(w_profile, w_post)
            weighted_union        += max(w_profile, w_post)

        if weighted_union == 0.0:
            return 0.0

        return weighted_intersection / weighted_union

    def community_similarity(
        self,
        profile: UserInterestProfile,
        post_communities: frozenset[str],
    ) -> float:
       
        if not profile.community_ids or not post_communities:
            return 0.0

        matched = profile.community_ids & post_communities
        return len(matched) / len(profile.community_ids)
