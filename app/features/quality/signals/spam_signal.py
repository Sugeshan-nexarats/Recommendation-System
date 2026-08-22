from __future__ import annotations
from app.features.quality.abstract_quality_signal import (AbstractQualitySignal, QualitySignalResult,)
from app.features.quality.quality_config import QualityConfig
from app.features.quality.quality_signal_registry import QualitySignalRegistry
from app.models.posts import Post
from app.retrievers.user_context import UserContext

@QualitySignalRegistry.register
class SpamSignal(AbstractQualitySignal):

    @property
    def name(self) -> str:
        return "spam"

    def compute(self, user: UserContext, post: Post, config: QualityConfig, ) -> QualitySignalResult:
     
        spam_prob = getattr(post, "spam_probability", None)
        
        if spam_prob is None:
            return QualitySignalResult(
                signal_name=self.name,
                score=1.0,
                metadata={"reason": "no_spam_data"},
            )
            
        spam_prob = min(max(spam_prob, 0.0), 1.0)
        score = 1.0 - spam_prob

        return QualitySignalResult(
            signal_name=self.name,
            score=round(score, 6),
            metadata={"spam_probability": round(spam_prob, 6)},
        )
