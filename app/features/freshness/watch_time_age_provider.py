"""
WatchTimeAgeProvider — proxy age estimator using aggregate watch time.

Proxy rationale:
    Newly published posts have had very little time for users to view them,
    so their aggregate watch_time is low.  As time passes and the post is
    surfaced to more users, watch_time grows.  This inverted relationship
    makes watch_time a usable — though imperfect — proxy for post age.

Conversion formula:
    Aggregate watch_time in seconds is assumed to grow at a platform-
    calibrated rate of SECONDS_PER_HOUR seconds of viewership per real
    calendar hour.  The formula:

        age_hours = watch_time_seconds / SECONDS_PER_HOUR

    where SECONDS_PER_HOUR = 3600 by convention (one second of watch time
    per real second, assuming one average viewer at a time).

    This is a deliberate over-simplification.  A viral post accumulates
    watch time much faster than a niche post.  The proxy will be replaced
    by real timestamps once they are available in the Post schema.

Proxy limitations (documented explicitly):
    - Viral posts appear older than they are (high watch_time → high age).
    - Niche posts appear newer than they are (low watch_time → low age).
    - The proxy ignores posting date entirely.

Replace with CreatedAtAgeProvider when Post.created_at is available.
"""

from __future__ import annotations

from app.features.freshness.abstract_age_provider import AbstractAgeProvider
from app.models.posts import Post

# Platform calibration: assumed watch-time accumulation rate.
# At 3600 s/h, one calendar hour corresponds to 3600 seconds of aggregate
# watch time (equivalent to one simultaneous viewer watching the whole hour).
# Adjust based on observed engagement data from analytics.
_WATCH_TIME_ACCUMULATION_RATE: float = 3_600.0  # seconds of watch_time per calendar hour


class WatchTimeAgeProvider(AbstractAgeProvider):
    """
    Estimates post age from aggregate watch_time seconds.

    Used as the default proxy until Post.created_at is available.
    See module docstring for limitations and replacement path.
    """

    @property
    def name(self) -> str:
        return "watch_time_proxy"

    @property
    def is_proxy(self) -> bool:
        return True

    def age_hours(self, post: Post) -> float:
        """
        Estimate age in hours from watch_time.

        Args:
            post: Post ORM object.

        Returns:
            Estimated age in fractional hours (>= 0).
            Returns 0.0 if watch_time is None or zero (post appears brand-new).
        """
        watch_time_seconds = float(post.watch_time or 0)
        if watch_time_seconds <= 0.0:
            return 0.0
        return watch_time_seconds / _WATCH_TIME_ACCUMULATION_RATE
