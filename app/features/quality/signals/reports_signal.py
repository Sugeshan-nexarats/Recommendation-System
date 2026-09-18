

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
class ReportsSignal(AbstractQualitySignal):
    """User report count penalty."""

    @property
    def name(self) -> str:
        return "reports"

    def compute(
        self,
        user: UserContext,
        post: Post,
        config: QualityConfig,
    ) -> QualitySignalResult:
        reports = getattr(post, "report_count", None) or 0
        cap = config.caps.reports
        
        # A post with reports >= cap gets a score of 0.0.
        penalty = min(float(reports) / cap, 1.0)
        score = 1.0 - penalty

        return QualitySignalResult(
            signal_name=self.name,
            score=round(score, 6),
            metadata={
                "report_count": int(reports),
                "cap": cap,
            },
        )
