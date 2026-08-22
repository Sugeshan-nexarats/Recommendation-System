"""
FollowingSignal — asymmetric following relationship proximity.

Signal semantics:
    A user who follows an author has expressed explicit, persistent interest
    in that creator's content.  Following is weaker than mutual friendship
    (it is unidirectional) but stronger than no connection.

Schema limitation:
    Post.author_id is not available.  The proxy uses the same friend-count
    field as FriendshipSignal but applies it only when user.following_ids
    is non-empty.  This means the signal degrades to the same count-based
    proxy as FriendshipSignal when both are active.

    When Post.author_id is available, the exact check is:
        score = 1.0 if post.author_id in user.following_ids else 0.0

Score formula (proxy):
    score = min(post.friends, cap.friends) / cap.friends
    → 0.0 if user follows no one or post has no friend connections.

Note: The proxy score will be identical to FriendshipSignal's when both
fire.  The weight difference in RelationshipConfig (friendship=3.0,
following=2.0) ensures they still contribute proportionally different
amounts to the final score.
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
