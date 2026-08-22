"""
MutualFriendsSignal — shared friends between user and post author.

Signal semantics:
    When a user shares many friends with a post's author, they likely move
    in the same social circles.  Mutual friends act as implicit social
    endorsements — "people I trust also know this creator."

    This is distinct from direct friendship (user IS friends with author)
    and measures indirect social proximity.

Data source:
    user.mutual_friend_ids — pre-computed by the Java application and
    provided in the UserContext.  It is expensive to compute at request
    time (requires graph traversal), so the Java app provides it as a
    pre-computed list for the N most relevant candidate authors.

Schema limitation:
    Without Post.author_id, we cannot verify which mutual friends relate
    to this specific post's author.  The proxy:

        score = min(len(user.mutual_friend_ids), cap.mutual) / cap.mutual

    This treats the breadth of the user's mutual-friend network as a proxy
    for the probability that this post's author is in it.

    When Post.author_id is available, the exact check is:
        author_mutual_friends = [f for f in user.mutual_friend_ids
                                   if f relates to post.author_id]
        score = min(len(author_mutual_friends), cap.mutual) / cap.mutual

Score formula (proxy):
    score = min(len(user.mutual_friend_ids), cap.mutual) / cap.mutual
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
class MutualFriendsSignal(AbstractRelationshipSignal):
    """Shared friend network depth as indirect social proximity."""

    @property
    def name(self) -> str:
        return "mutual_friends"

    def compute(
        self,
        user: UserContext,
        post: Post,
        config: RelationshipConfig,
    ) -> RelationshipSignalResult:
        if not user.mutual_friend_ids:
            return RelationshipSignalResult(
                signal_name=self.name,
                score=0.0,
                metadata={"reason": "no_mutual_friend_data"},
            )

        mutual_count = float(len(user.mutual_friend_ids))
        cap          = config.caps.mutual
        score        = min(mutual_count, cap) / cap

        return RelationshipSignalResult(
            signal_name=self.name,
            score=round(score, 6),
            metadata={
                "mutual_friend_count": int(mutual_count),
                "cap":                 cap,
                "proxy_mode":          True,
                "proxy_note":          (
                    "Counts total mutual friends in network, not author-specific. "
                    "Requires Post.author_id for exact calculation."
                ),
            },
        )
