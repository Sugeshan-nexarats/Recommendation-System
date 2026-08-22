from __future__ import annotations
from app.features.quality.abstract_quality_signal import (AbstractQualitySignal, QualitySignalResult,)
from app.features.quality.quality_config import QualityConfig
from app.features.quality.quality_signal_registry import QualitySignalRegistry
from app.models.posts import Post
from app.retrievers.user_context import UserContext

@QualitySignalRegistry.register
class DuplicateSignal(AbstractQualitySignal):
    """Duplicate post penalty."""

    @property
    def name(self) -> str:
        return "duplicate"

    def compute(
        self,
        user: UserContext,
        post: Post,
        config: QualityConfig,
    ) -> QualitySignalResult:
        is_duplicate = getattr(post, "is_duplicate", None)
        
        if is_duplicate is None:
            return QualitySignalResult(
                signal_name=self.name,
                score=1.0, # Default to not duplicate
                metadata={"reason": "no_duplicate_data"},
            )
            
        score = 0.0 if is_duplicate else 1.0

        return QualitySignalResult(
            signal_name=self.name,
            score=round(score, 6),
            metadata={"is_duplicate": bool(is_duplicate)},
        )
