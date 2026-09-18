
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


    @property
    def name(self) -> str:
        return "creator_relationship"

    def compute(
        self,
        user: UserContext,
        post: Post,
        config: RelationshipConfig,
    ) -> RelationshipSignalResult:
       
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

       
        if not user.user_relationships:
            return RelationshipSignalResult(
                signal_name=self.name,
                score=0.0,
                metadata={
                    "reason":     "no_user_relationships",
                    "creator_id": creator_id,
                },
            )

       
        best_type: str | None = None
        best_priority: int = -1

        viewer_id = user.user_id

        for rel in user.user_relationships:
           
            if rel.status != STATUS_ACCEPTED:
                continue

           
            if rel.requester_user_id == viewer_id and rel.target_user_id == creator_id:
                other_is_creator = True
            elif rel.target_user_id == viewer_id and rel.requester_user_id == creator_id:
               
                other_is_creator = rel.relationship_type == RELATIONSHIP_TYPE_FRIEND
            else:
                other_is_creator = False

            if not other_is_creator:
                continue

            priority = _TYPE_PRIORITY.get(rel.relationship_type, 0)
            if priority > best_priority:
                best_priority = priority
                best_type = rel.relationship_type

        
        scores = config.creator_scores
        if best_type == RELATIONSHIP_TYPE_FRIEND:
            score = scores.friend_score
        elif best_type == RELATIONSHIP_TYPE_FOLLOW:
            score = scores.following_score
        else:
            score = scores.default_score

        
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
