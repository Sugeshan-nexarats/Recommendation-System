"""
CommunitySignal — shared community membership overlap.

Signal semantics:
    A post published in a community the user belongs to is significantly
    more likely to be relevant than one from an unknown community.
    Community membership is an explicit, persistent social decision with
    high signal quality.

Algorithm (recall-oriented):
    score = |user.community_ids ∩ post.communities| / |user.community_ids|

    Recall from the user's perspective: "what fraction of the user's
    communities does this post belong to?"

    Recall is preferred over precision here because:
      - A post may belong to many communities (precision denominator grows).
      - We care about coverage of the user's community life, not how niche
        the post is within its community set.

No schema limitation:
    post.communities is a JSON list of community IDs from the Java app.
    user.community_ids are the user's subscribed community IDs.
    Both are normalised to str for safe comparison.
"""

from __future__ import annotations

from app.features.relationship.abstract_relationship_signal import (
    AbstractRelationshipSignal,
    RelationshipSignalResult,
)
from app.features.relationship.relationship_config import RelationshipConfig
from app.features.relationship.relationship_signal_registry import RelationshipSignalRegistry
from app.models.posts import Post
from app.retrievers.user_context import UserContext


@RelationshipSignalRegistry.register
class CommunitySignal(AbstractRelationshipSignal):
    """Community membership overlap between user and post."""

    @property
    def name(self) -> str:
        return "community"

    def compute(
        self,
        user: UserContext,
        post: Post,
        config: RelationshipConfig,
    ) -> RelationshipSignalResult:
        if not user.community_ids:
            return RelationshipSignalResult(
                signal_name=self.name,
                score=0.0,
                metadata={"reason": "user_in_no_communities"},
            )

        user_communities: frozenset[str] = frozenset(str(c) for c in user.community_ids)
        post_communities: frozenset[str] = frozenset(
            str(c) for c in (post.communities or [])
        )

        if not post_communities:
            return RelationshipSignalResult(
                signal_name=self.name,
                score=0.0,
                metadata={
                    "user_community_count": len(user_communities),
                    "post_community_count": 0,
                    "matched_communities":  [],
                },
            )

        matched = user_communities & post_communities
        score   = len(matched) / len(user_communities)

        return RelationshipSignalResult(
            signal_name=self.name,
            score=round(score, 6),
            metadata={
                "matched_communities":  sorted(matched),
                "user_community_count": len(user_communities),
                "post_community_count": len(post_communities),
                "overlap_count":        len(matched),
            },
        )
