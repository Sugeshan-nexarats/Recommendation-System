
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
