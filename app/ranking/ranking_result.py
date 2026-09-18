

from __future__ import annotations

from dataclasses import dataclass, field

from app.models.posts import Post


@dataclass(frozen=True, slots=True)
class RankingResult:


    post: Post
    rank: int
    score: float
    feature_breakdown: dict[str, float] = field(default_factory=dict)
