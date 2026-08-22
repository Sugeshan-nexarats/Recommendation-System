"""
RankingInput — the RankingEngine's typed input contract.

Carries exactly the data the RankingEngine needs and nothing more.
By accepting (Post, list[FeatureResult]) rather than a raw FeedRequest
or database session, the RankingEngine is kept completely independent of
the retrieval and feature-computation stages.

This value object also serves as the natural test fixture boundary:
unit tests for the RankingEngine construct RankingInputs directly,
with no database, no HTTP layer, and no FeatureRegistry required.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.features.abstract_feature import FeatureResult
from app.models.posts import Post


@dataclass(frozen=True, slots=True)
class RankingInput:
    """
    A single candidate post together with its computed feature vector.

    Attributes:
        post:            The ORM Post object to be ranked.
        feature_results: Ordered list of FeatureResult objects produced by
                         the Feature Framework (Stage 3).  The RankingEngine
                         reads feature_name and score from each entry to
                         compute the final relevance score.
    """

    post: Post
    feature_results: list[FeatureResult] = field(default_factory=list)
