"""
PastInteractionSignal — previous engagement with the post's author.

Signal semantics:
    A user who has previously liked, commented on, or shared posts by an
    author has demonstrated affinity with that creator.  Content from
    previously-engaged authors is more likely to be relevant.

Algorithm:
    The Java application provides user.interacted_author_ids — the IDs of
    authors whose posts the user has interacted with in the recent past.

    If the post's author ID were available (Post.author_id), the score would be:
        score = 1.0 if post.author_id in user.interacted_author_ids else 0.0

Schema limitation:
    Post.author_id is not in the current model.  The proxy: we check if the
    post has any friend connections (post.friends > 0) and the user has any
    previous interactions — a weak but non-zero signal.

    When Post.author_id is available:
        score = 1.0 if post.author_id in user.interacted_author_ids else 0.0

Score formula (proxy):
    has_interactions = len(user.interacted_author_ids) > 0
    post_is_connected = post.friends > 0
    score = min(len(user.interacted_author_ids), cap.interactions) / cap.interactions
              if post_is_connected else 0.0
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

        # Proxy: require the post to have social graph connections before
        # awarding interaction score — prevents awarding credit to isolated posts.
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
