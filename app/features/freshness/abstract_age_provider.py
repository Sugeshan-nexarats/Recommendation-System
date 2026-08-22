from __future__ import annotations
from abc import ABC, abstractmethod
from app.models.posts import Post

class AbstractAgeProvider(ABC):
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name for metadata attribution."""
        ...

    @property
    @abstractmethod
    def is_proxy(self) -> bool:
        """
        True when this provider uses a proxy field rather than a real
        timestamp.
        """
        ...

    @abstractmethod
    def age_hours(self, post: Post) -> float:
        """
        Estimate the post's age in fractional hours.
        """
        ...
