"""
AbstractAgeProvider — Strategy interface for extracting post age.

This is the seam that isolates FreshnessFeature from the Post schema.

Current state:
    The Post model has no ``created_at`` timestamp.  WatchTimeAgeProvider
    uses ``watch_time`` (aggregate seconds of viewership) as a proxy for
    engagement recency.

Future state:
    When the Java application populates ``created_at`` and the SQLAlchemy
    model is updated, add CreatedAtAgeProvider and inject it — zero changes
    to FreshnessFeature or any other code.

Migration path:
    1. Add ``created_at = Column(DateTime(timezone=True))`` to Post.
    2. Implement CreatedAtAgeProvider (see docstring below).
    3. In recommend_route.py, swap the injected provider:
           FreshnessFeature(age_provider=CreatedAtAgeProvider())
    4. Delete WatchTimeAgeProvider once all posts have populated timestamps.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.models.posts import Post


class AbstractAgeProvider(ABC):
    """
    Extracts the estimated age of a post in fractional hours.

    Implementations MUST:
      - Return a non-negative float (0.0 means brand-new).
      - Never raise — return a large sentinel value (e.g. float('inf'))
        to signal that the age cannot be determined; callers treat this
        as maximally stale.
      - Be stateless and safe for concurrent use.
    """

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
        timestamp.  Included in FeatureResult.metadata so engineers can
        filter results by data quality in dashboards.
        """
        ...

    @abstractmethod
    def age_hours(self, post: Post) -> float:
        """
        Estimate the post's age in fractional hours.

        Args:
            post: The Post ORM object.

        Returns:
            Non-negative float representing age in hours.
            Returns float('inf') if age cannot be determined.

        Example (future CreatedAtAgeProvider):
            from datetime import timezone, datetime
            now = datetime.now(tz=timezone.utc)
            delta = now - post.created_at
            return delta.total_seconds() / 3600
        """
        ...
