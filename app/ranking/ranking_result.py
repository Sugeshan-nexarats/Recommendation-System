"""
RankingResult — the RankingEngine's typed output contract.

Each RankingResult represents one post after the full ranking pass:
  - Its final relevance score (from the scoring strategy).
  - Its 1-indexed rank position within the sorted list.
  - A feature breakdown showing each feature's weighted contribution —
    essential for explainability, debugging, and A/B experiment auditing.

The FeedEngine maps RankingResult → RankedPost (the public API schema).
Keeping RankingResult as an internal domain type means the schema layer
can evolve independently of the ranking internals.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.models.posts import Post


@dataclass(frozen=True, slots=True)
class RankingResult:
    """
    Output of the RankingEngine for a single candidate post.

    Attributes:
        post:              The ranked ORM Post object.
        rank:              1-indexed position in the final sorted list.
                           rank=1 is the most relevant post.
        score:             Final relevance score ∈ [0.0, 1.0] produced by
                           the active scoring strategy.
        feature_breakdown: Mapping of feature_name → weighted contribution
                           to the final score.  All values are non-negative
                           and the dict sums to approximately ``score``.
                           Used for explainability and offline analysis.
    """

    post: Post
    rank: int
    score: float
    feature_breakdown: dict[str, float] = field(default_factory=dict)
