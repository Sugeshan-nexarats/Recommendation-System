from __future__ import annotations
from app.features.quality.abstract_quality_signal import (AbstractQualitySignal, QualitySignalResult,)
from app.features.quality.quality_config import QualityConfig
from app.features.quality.quality_signal_registry import QualitySignalRegistry
from app.models.posts import Post
from app.retrievers.user_context import UserContext

@QualitySignalRegistry.register
class ReputationSignal(AbstractQualitySignal):
    """Creator reputation quality signal."""

    @property
    def name(self) -> str:
        return "reputation"

    def compute(self,user: UserContext, post: Post, config: QualityConfig,) -> QualitySignalResult:
        
        reputation = getattr(post, "creator_reputation", None)
        
        if reputation is None:
            return QualitySignalResult(
                signal_name=self.name,
                score=0.5, # Neutral fallback
                metadata={"reason": "no_reputation_data"},
            )
            
        score = min(max(reputation, 0.0), 1.0)

        return QualitySignalResult(
            signal_name=self.name,
            score=round(score, 6),
            metadata={"creator_reputation": round(score, 6)},
        )
