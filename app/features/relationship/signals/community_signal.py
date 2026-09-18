
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
