"""
CreatorRelationshipSignal — exact author-match relationship signal.

Signal semantics:
    Checks whether the requesting user has a direct ACCEPTED relationship with
    the post's creator (post.creator_id).

    This is an exact, direct signal using real relationship data from the
    user_relationships table, as opposed to the proxy-mode signals
    (FriendshipSignal, FollowingSignal) which use the aggregate post.friends
    count because post.creator_id was historically unavailable.

Algorithm:
    1. If post.creator_id is None → score = 0.0 (no author data).
    2. Look up creator_id in user.user_relationships.
    3. Only ACCEPTED relationships contribute a positive score.
       PENDING, REJECTED, BLOCKED, REMOVED → treated as no relationship (0.0).
    4. Return score based on the best accepted relationship type found:
         FRIEND    → config scores for friend relationship (default: 1.0)
         FOLLOW    → config scores for following relationship (default: 0.8)
         no match  → config scores for default (default: 0.0)
    5. Bidirectional FRIEND handling: a FRIEND row where the viewer is either
       the requester OR the target counts as a friendship (the relationship
       repo's get_by_user_id() already returns both directions, so this signal
       only needs to check target_user_id == creator_id OR
       requester_user_id == creator_id).
    6. Clamp to [0.0, 1.0].

Score configuration:
    Scores are NOT hardcoded.  They are read from RelationshipConfig
    (via the nested RelationshipCreatorScores model).  Defaults:
        friend_score    = 1.0
        following_score = 0.8
        default_score   = 0.0

    Inject a custom RelationshipConfig to A/B test different values without
    touching this signal.

Signal name:
    "creator_relationship"
    Must match the weight key in RelationshipSignalWeights.
"""

from __future__ import annotations

import logging

from app.features.relationship.abstract_relationship_signal import (
    AbstractRelationshipSignal,
    RelationshipSignalResult,
)
from app.features.relationship.relationship_config import RelationshipConfig
from app.features.relationship.relationship_signal_registry import RelationshipSignalRegistry
from app.models.posts import Post
from app.models.user_relationship import (
    RELATIONSHIP_TYPE_FOLLOW,
    RELATIONSHIP_TYPE_FRIEND,
    STATUS_ACCEPTED,
)
from app.retrievers.user_context import UserContext

logger = logging.getLogger(__name__)

# Score precedence: FRIEND beats FOLLOW if somehow both appear for the same pair.
_TYPE_PRIORITY: dict[str, int] = {
    RELATIONSHIP_TYPE_FRIEND: 2,
    RELATIONSHIP_TYPE_FOLLOW:  1,
}


@RelationshipSignalRegistry.register
class CreatorRelationshipSignal(AbstractRelationshipSignal):
    """
    Exact creator-to-user relationship signal.

    High score (1.0)   → user has an ACCEPTED FRIEND relationship with the creator.
    Medium score (0.8) → user has an ACCEPTED FOLLOW relationship with the creator.
    Low score (0.0)    → no accepted relationship, or post.creator_id unavailable.

    PENDING / REJECTED / BLOCKED / REMOVED relationships return 0.0.
    """

    @property
    def name(self) -> str:
        return "creator_relationship"

    def compute(
        self,
        user: UserContext,
        post: Post,
        config: RelationshipConfig,
    ) -> RelationshipSignalResult:
        # ── Guard: creator_id must be present on the post ─────────────
        creator_id: int | None = getattr(post, "creator_id", None)
        if creator_id is None:
            return RelationshipSignalResult(
                signal_name=self.name,
                score=0.0,
                metadata={
                    "reason":  "creator_id_unavailable",
                    "post_id": getattr(post, "post_id", None),
                },
            )

        # ── Guard: user must have relationship data ────────────────────
        if not user.user_relationships:
            return RelationshipSignalResult(
                signal_name=self.name,
                score=0.0,
                metadata={
                    "reason":     "no_user_relationships",
                    "creator_id": creator_id,
                },
            )

        # ── Find the best ACCEPTED relationship with the creator ───────
        # The repository's get_by_user_id() already includes both:
        #   - Outgoing: viewer is requester_user_id
        #   - Incoming FRIEND: viewer is target_user_id (for accepted friendships)
        # So we just need to find rows where the OTHER party is the creator.
        best_type: str | None = None
        best_priority: int = -1

        viewer_id = user.user_id

        for rel in user.user_relationships:
            # Only ACCEPTED relationships contribute a positive score.
            if rel.status != STATUS_ACCEPTED:
                continue

            # Determine if this relationship involves the creator.
            # The "other" user in the relationship (not the viewer) must be the creator.
            if rel.requester_user_id == viewer_id and rel.target_user_id == creator_id:
                other_is_creator = True
            elif rel.target_user_id == viewer_id and rel.requester_user_id == creator_id:
                # Reverse direction — only valid for FRIEND (bidirectional)
                other_is_creator = rel.relationship_type == RELATIONSHIP_TYPE_FRIEND
            else:
                other_is_creator = False

            if not other_is_creator:
                continue

            priority = _TYPE_PRIORITY.get(rel.relationship_type, 0)
            if priority > best_priority:
                best_priority = priority
                best_type = rel.relationship_type

        # ── Score based on the best relationship type ──────────────────
        scores = config.creator_scores
        if best_type == RELATIONSHIP_TYPE_FRIEND:
            score = scores.friend_score
        elif best_type == RELATIONSHIP_TYPE_FOLLOW:
            score = scores.following_score
        else:
            score = scores.default_score

        # Clamp to [0.0, 1.0] — safety guard.
        score = min(max(score, 0.0), 1.0)

        logger.debug(
            "CreatorRelationshipSignal: post_id=%s creator_id=%s "
            "best_relationship_type=%s score=%.4f",
            getattr(post, "post_id", "?"),
            creator_id,
            best_type,
            score,
        )

        return RelationshipSignalResult(
            signal_name=self.name,
            score=round(score, 6),
            metadata={
                "creator_id":              creator_id,
                "relationship_type":       best_type,
                "relationship_score":      round(score, 6),
                "user_relationship_count": len(user.user_relationships),
            },
        )
