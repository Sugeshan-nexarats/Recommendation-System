
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
class FollowingSignal(AbstractRelationshipSignal):
    """Asymmetric follow relationship proximity."""

    @property
    def name(self) -> str:
        return "following"

    def compute(
        self,
        user: UserContext,
        post: Post,
        config: RelationshipConfig,
    ) -> RelationshipSignalResult:
        if not user.following_ids:
            return RelationshipSignalResult(
                signal_name=self.name,
                score=0.0,
                metadata={"reason": "user_follows_nobody"},
            )

        post_friends = float(post.friends or 0)
        cap          = config.caps.friends
        score        = min(post_friends, cap) / cap

        return RelationshipSignalResult(
            signal_name=self.name,
            score=round(score, 6),
            metadata={
                "post_friend_count":  int(post_friends),
                "user_following_count": len(user.following_ids),
                "cap":                cap,
                "proxy_mode":         True,
                "proxy_note":         "Exact author match unavailable without Post.author_id.",
            },
        )
