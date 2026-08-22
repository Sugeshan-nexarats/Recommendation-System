"""
FriendshipSignal — bidirectional friend connection proximity.

Signal semantics:
    Measures whether the post originates from within the user's mutual
    friend network.  A post connected to many of the user's friends
    scores higher than one connected to few.

Schema limitation:
    Post.friends is an aggregate count, not a list of friend IDs.
    We cannot verify exact overlap with user.friend_ids today.
    The proxy: if user has friends AND post has a non-zero friend count,
    treat the post as socially proximate.  Score scales with friend count
    up to the configured cap.

    When Post.author_id is available, replace this with an exact check:
        score = 1.0 if post.author_id in user.friend_ids else 0.0

Score formula (proxy):
    score = min(post.friends, cap.friends) / cap.friends
    → 0.0 if user has no friends or post has no friend connections.
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
