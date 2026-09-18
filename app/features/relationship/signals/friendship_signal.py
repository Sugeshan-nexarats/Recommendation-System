
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
class FriendshipSignal(AbstractRelationshipSignal):
    """Bidirectional friend connection strength."""

    @property
    def name(self) -> str:
        return "friendship"

    def compute(
        self,
        user: UserContext,
        post: Post,
        config: RelationshipConfig,
    ) -> RelationshipSignalResult:
        if not user.friend_ids:
            return RelationshipSignalResult(
                signal_name=self.name,
                score=0.0,
                metadata={"reason": "user_has_no_friends"},
            )

        post_friends = float(post.friends or 0)
        cap          = config.caps.friends
        score        = min(post_friends, cap) / cap

        return RelationshipSignalResult(
            signal_name=self.name,
            score=round(score, 6),
            metadata={
                "post_friend_count": int(post_friends),
                "user_friend_count": len(user.friend_ids),
                "cap":               cap,
                "proxy_mode":        True,
                "proxy_note":        "Post.friends is a count, not a list — exact overlap unavailable.",
            },
        )
