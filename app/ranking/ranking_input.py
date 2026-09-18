
from __future__ import annotations

from dataclasses import dataclass, field

from app.features.abstract_feature import FeatureResult
from app.models.posts import Post


@dataclass(frozen=True, slots=True)
class RankingInput:


    post: Post
    feature_results: list[FeatureResult] = field(default_factory=list)
