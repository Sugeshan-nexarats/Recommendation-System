"""
AbstractQualitySignal — plugin interface for individual quality signals.

Adding a new signal type:
    1. Create app/features/quality/signals/my_signal.py implementing this interface.
    2. Decorate with @QualitySignalRegistry.register.
    3. Add a default weight to QualitySignalWeights in quality_config.py.
    4. Import the module in app/features/quality/signals/__init__.py.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from app.features.quality.quality_config import QualityConfig
from app.models.posts import Post
from app.retrievers.user_context import UserContext


@dataclass(frozen=True, slots=True)
class QualitySignalResult:
    """
    Output of a single quality signal computation.
    """
    signal_name: str
    score: float                                    # ∈ [0.0, 1.0]
    metadata: dict[str, Any] = field(default_factory=dict)


class AbstractQualitySignal(ABC):

    @property
    @abstractmethod
    def name(self) -> str:
        
        ...

    @abstractmethod
    def compute(self, user: UserContext, post: Post, config: QualityConfig, ) -> QualitySignalResult:
        """
        Compute the quality score for a (user, post) pair.
        """
        ...
