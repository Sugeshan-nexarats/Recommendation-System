

from __future__ import annotations

from app.features.quality.abstract_quality_signal import (
    AbstractQualitySignal,
    QualitySignalResult,
)
from app.features.quality.quality_config import QualityConfig
from app.features.quality.quality_signal_registry import QualitySignalRegistry
from app.models.posts import Post
from app.retrievers.user_context import UserContext


@QualitySignalRegistry.register
class ContentQualitySignal(AbstractQualitySignal):
    """Engagement-ratio based content quality signal."""

    @property
    def name(self) -> str:
        return "content"

    def compute(
        self,
        user: UserContext,
        post: Post,
        config: QualityConfig,
    ) -> QualitySignalResult:
        likes    = post.likes    or 0
        comments = post.comments or 0
        saves    = post.saves    or 0

        denominator = max(likes, 1)
        save_rate       = min(saves / denominator, 1.0)
        discussion_rate = min(comments / denominator, 1.0)

        score = (save_rate + discussion_rate) / 2.0

        return QualitySignalResult(
            signal_name=self.name,
            score=round(score, 6),
            metadata={
                "save_rate":       round(save_rate, 6),
                "discussion_rate": round(discussion_rate, 6),
                "likes":           likes,
                "comments":        comments,
                "saves":           saves,
            },
        )
