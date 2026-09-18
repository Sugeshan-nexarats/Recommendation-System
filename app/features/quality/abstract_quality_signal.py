

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from app.features.quality.quality_config import QualityConfig
from app.models.posts import Post
from app.retrievers.user_context import UserContext


@dataclass(frozen=True, slots=True)
class QualitySignalResult:

    signal_name: str
    score: float                                    # ∈ [0.0, 1.0]
    metadata: dict[str, Any] = field(default_factory=dict)


class AbstractQualitySignal(ABC):

    @property
    @abstractmethod
    def name(self) -> str:
 
        ...

    @abstractmethod
    def compute(
        self,
        user: UserContext,
        post: Post,
        config: QualityConfig,
    ) -> QualitySignalResult:
  
        ...
