
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
class PastInteractionSignal(AbstractRelationshipSignal):
    """Prior engagement with the post's author as a social proximity signal."""

    @property
    def name(self) -> str:
        return "past_interaction"

    def compute(
        self,
        user: UserContext,
        post: Post,
        config: RelationshipConfig,
    ) -> RelationshipSignalResult:
        if not user.interacted_author_ids:
            return RelationshipSignalResult(
                signal_name=self.name,
                score=0.0,
                metadata={"reason": "no_interaction_history"},
            )

     
        post_connected = (post.friends or 0) > 0
        if not post_connected:
            return RelationshipSignalResult(
                signal_name=self.name,
                score=0.0,
                metadata={
                    "reason":                    "post_not_socially_connected",
                    "interacted_author_count":   len(user.interacted_author_ids),
                    "proxy_mode":                True,
                },
            )

        interaction_count = float(len(user.interacted_author_ids))
        cap               = config.caps.interactions
        score             = min(interaction_count, cap) / cap

        return RelationshipSignalResult(
            signal_name=self.name,
            score=round(score, 6),
            metadata={
                "interacted_author_count": int(interaction_count),
                "cap":                     cap,
                "proxy_mode":              True,
                "proxy_note":              "Exact author match unavailable without Post.author_id.",
            },
        )
