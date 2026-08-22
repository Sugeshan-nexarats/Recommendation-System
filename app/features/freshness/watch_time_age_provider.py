from __future__ import annotations
from app.features.freshness.abstract_age_provider import AbstractAgeProvider
from app.models.posts import Post

_WATCH_TIME_ACCUMULATION_RATE: float = 3_600.0  


class WatchTimeAgeProvider(AbstractAgeProvider):

    @property
    def name(self) -> str:
        return "watch_time_proxy"

    @property
    def is_proxy(self) -> bool:
        return True

    def age_hours(self, post: Post) -> float:
        
        watch_time_seconds = float(post.watch_time or 0)
        if watch_time_seconds <= 0.0:
            return 0.0
        return watch_time_seconds / _WATCH_TIME_ACCUMULATION_RATE
