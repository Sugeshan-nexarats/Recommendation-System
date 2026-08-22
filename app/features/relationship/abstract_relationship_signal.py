"""
AbstractRelationshipSignal — plugin interface for individual relationship signals.

This is the extension point that satisfies "new relationship types can be
added without modifying existing code."

Adding a new signal type:
    1. Create app/features/relationship/signals/my_signal.py
       implementing AbstractRelationshipSignal.
    2. Decorate with @RelationshipSignalRegistry.register.
    3. Add a default weight to RelationshipSignalWeights in relationship_config.py.
    4. Import the module in app/features/relationship/signals/__init__.py.

That is the complete changeset.  RelationshipFeature, RelationshipSignalRegistry,
and all other signals are untouched.

Contract:
    compute(user, post, config) → RelationshipSignalResult
      - score ∈ [0.0, 1.0]
      - Never raises — catch internally and return score=0.0
      - Stateless and safe for concurrent use
      - No I/O — all data arrives via UserContext and Post

Signal naming convention:
    Signal names must match the weight key in RelationshipSignalWeights.
    e.g. FriendshipSignal.name = "friendship"
         → config.weights.friendship is the weight applied to its score.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from app.features.relationship.relationship_config import RelationshipConfig
from app.models.posts import Post
from app.retrievers.user_context import UserContext


# ---------------------------------------------------------------------------
# Result value object
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class RelationshipSignalResult:
    """
    Output of a single relationship signal computation.

    Attributes:
        signal_name: Canonical name matching the weight key in
                     RelationshipSignalWeights (e.g. "friendship").
        score:       Normalised signal strength ∈ [0.0, 1.0].
        metadata:    Diagnostic data for explainability (JSON-serialisable).
    """

    signal_name: str
    score: float                                    # ∈ [0.0, 1.0]
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Abstract interface
# ---------------------------------------------------------------------------


class AbstractRelationshipSignal(ABC):
    """
    Plugin interface for a single social-graph relationship signal.

    Each concrete signal measures one dimension of the social relationship
    between the requesting user and the post's content/author.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Canonical signal name.  Must match a weight key in
        RelationshipSignalWeights (e.g. 'friendship', 'community').
        Used as the registry key and as RelationshipSignalResult.signal_name.
        """
        ...

    @abstractmethod
    def compute(
        self,
        user: UserContext,
        post: Post,
        config: RelationshipConfig,
    ) -> RelationshipSignalResult:
        """
        Compute the relationship signal score for a (user, post) pair.

        Args:
            user:   Immutable user context with social graph data.
            post:   Candidate post being evaluated.
            config: Active RelationshipConfig (weights and caps).

        Returns:
            RelationshipSignalResult with score ∈ [0.0, 1.0].
        """
        ...
