"""
RelationshipConfig — injectable, validated weight configuration for
RelationshipFeature's signal registry.

Design principles:
    1. All weights are data, not code.  Changing signal importance is a
       config change, not a code change.
    2. Weights do not need to sum to any specific value — they are
       automatically normalised by RelationshipFeature.
    3. New signals added to the registry can declare their own default
       weight here.  If a signal is not listed, it receives weight=0 and
       is silently ignored — safe for rolling deployments.
    4. Validated at construction time via Pydantic.

Signal weight rationale:
    creator_relationship > Friendship > Community > Following > MutualFriends > PastInteraction

    creator_relationship is the highest because it is a direct, exact
    author-match using real user_relationships table data, not a proxy
    count like post.friends.  It is the most precise social signal
    currently available.

    Mutual friends and past interactions are weaker signals because:
      - mutual_friend_ids is pre-computed and may be stale.
      - past_interaction_ids require historical data not always available.

    Friendship and community are the strongest proxy-mode signals because
    they represent explicit, persistent social decisions by the user.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

# ---------------------------------------------------------------------------
# Default weights — tuned for a social-first platform.
# Higher = stronger influence on final score.
# ---------------------------------------------------------------------------

_DEFAULT_WEIGHT_CREATOR_RELATIONSHIP: float = 4.0
_DEFAULT_WEIGHT_FRIENDSHIP:           float = 3.0
_DEFAULT_WEIGHT_FOLLOWING:            float = 2.0
_DEFAULT_WEIGHT_COMMUNITY:            float = 2.5
_DEFAULT_WEIGHT_MUTUAL_FRIENDS:       float = 1.5
_DEFAULT_WEIGHT_PAST_INTERACTION:     float = 1.0

# ---------------------------------------------------------------------------
# Per-signal caps (for signals that use count-based proximity scores)
# ---------------------------------------------------------------------------

_DEFAULT_CAP_FRIENDS:              float = 500.0   # friend count ceiling
_DEFAULT_CAP_MUTUAL_FRIENDS:       float = 50.0    # mutual friend count ceiling
_DEFAULT_CAP_INTERACTIONS:         float = 20.0    # past-interaction author count

# ---------------------------------------------------------------------------
# Creator-relationship score values
# ---------------------------------------------------------------------------

_DEFAULT_CREATOR_SCORE_FRIEND:    float = 1.0   # user is a friend of the creator
_DEFAULT_CREATOR_SCORE_FOLLOWING: float = 0.8   # user follows the creator
_DEFAULT_CREATOR_SCORE_DEFAULT:   float = 0.0   # no relationship


class RelationshipCreatorScores(BaseModel):
    """
    Score values for the CreatorRelationshipSignal.

    These are the raw scores returned when a relationship is found between
    the requesting user and a post's creator:

        friend_score    — requesting user has a "friend" relationship
                          with the creator.  Default: 1.0
        following_score — requesting user is "following" the creator.
                          Default: 0.8
        default_score   — no relationship found, or creator_id unavailable.
                          Default: 0.0

    All scores are clamped to [0.0, 1.0] by the signal implementation.
    Inject a custom config to A/B test different values without modifying
    CreatorRelationshipSignal.
    """

    friend_score:    float = Field(default=_DEFAULT_CREATOR_SCORE_FRIEND,    ge=0.0, le=1.0)
    following_score: float = Field(default=_DEFAULT_CREATOR_SCORE_FOLLOWING, ge=0.0, le=1.0)
    default_score:   float = Field(default=_DEFAULT_CREATOR_SCORE_DEFAULT,   ge=0.0, le=1.0)

    model_config = {"frozen": True}


class RelationshipSignalWeights(BaseModel):
    """
    Relative importance weight for each relationship signal.

    All weights must be >= 0.  At least one must be > 0.
    The weights are normalised automatically by RelationshipFeature so
    their absolute values do not matter — only their ratios do.

    Extend this model when adding new relationship signal types so their
    default weight is explicit, documented, and validated.
    """

    creator_relationship: float = Field(default=_DEFAULT_WEIGHT_CREATOR_RELATIONSHIP, ge=0.0)
    friendship:           float = Field(default=_DEFAULT_WEIGHT_FRIENDSHIP,            ge=0.0)
    following:            float = Field(default=_DEFAULT_WEIGHT_FOLLOWING,             ge=0.0)
    community:            float = Field(default=_DEFAULT_WEIGHT_COMMUNITY,             ge=0.0)
    mutual_friends:       float = Field(default=_DEFAULT_WEIGHT_MUTUAL_FRIENDS,        ge=0.0)
    past_interaction:     float = Field(default=_DEFAULT_WEIGHT_PAST_INTERACTION,      ge=0.0)

    model_config = {"frozen": True}


class RelationshipSignalCaps(BaseModel):
    """
    Normalisation caps for count-based signals.

    Signals that use raw counts (e.g. number of mutual friends) divide
    by the cap to produce a [0, 1] score before weighting.
    """

    friends:      float = Field(default=_DEFAULT_CAP_FRIENDS,         gt=0.0)
    mutual:       float = Field(default=_DEFAULT_CAP_MUTUAL_FRIENDS,   gt=0.0)
    interactions: float = Field(default=_DEFAULT_CAP_INTERACTIONS,     gt=0.0)

    model_config = {"frozen": True}


class RelationshipConfig(BaseModel):
    """
    Complete, immutable configuration for RelationshipFeature.

    Attributes:
        weights:        Per-signal importance weights.
        caps:           Normalisation caps for count-based signals.
        creator_scores: Score values for CreatorRelationshipSignal
                        (friend / following / no-relation).
    """

    weights:        RelationshipSignalWeights  = Field(default_factory=RelationshipSignalWeights)
    caps:           RelationshipSignalCaps     = Field(default_factory=RelationshipSignalCaps)
    creator_scores: RelationshipCreatorScores  = Field(default_factory=RelationshipCreatorScores)

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def at_least_one_positive_weight(self) -> "RelationshipConfig":
        """Reject all-zero configs — they produce NaN scores."""
        w = self.weights
        total = (
            w.creator_relationship + w.friendship + w.following + w.community
            + w.mutual_friends + w.past_interaction
        )
        if total == 0.0:
            raise ValueError(
                "RelationshipConfig: all signal weights are zero.  "
                "At least one weight must be > 0."
            )
        return self

    @property
    def total_weight(self) -> float:
        """Sum of all signal weights — normalisation denominator."""
        w = self.weights
        return (
            w.creator_relationship + w.friendship + w.following + w.community
            + w.mutual_friends + w.past_interaction
        )
