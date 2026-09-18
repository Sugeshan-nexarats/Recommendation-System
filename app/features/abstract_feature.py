from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any
from app.models.posts import Post
from app.retrievers.user_context import UserContext

if TYPE_CHECKING:
    from app.signals.signal_context import SignalContext


@dataclass(frozen=True, slots=True)
class FeatureResult:
    

    feature_name: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)



class AbstractFeature(ABC):

    @property
    @abstractmethod
    def name(self) -> str:
 
        ...

    @abstractmethod
    def compute(
        self,
        user: UserContext,
        post: Post,
        signal_context: "SignalContext | None" = None,
    ) -> FeatureResult:
        ...

