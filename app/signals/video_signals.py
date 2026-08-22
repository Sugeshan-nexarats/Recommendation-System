from __future__ import annotations
import logging
from app.models.posts import Post
from app.signals.signal_context import SignalContext

logger = logging.getLogger(__name__)

_CONTENT_TYPE = "video"


class VideoSignals:
    
    @property
    def name(self) -> str:
        return "VideoSignals"

    def extract(self, post: Post) -> SignalContext:
        signals = {
            "watch_time": post.watch_time or 0,
            "likes":      post.likes      or 0,
            "shares":     post.shares     or 0,
            "saves":      post.saves      or 0,
            "comments":   post.comments   or 0,
            "friends":    post.friends    or 0,
        }

        logger.debug(
            "VideoSignals: extracted signals for post_id=%s content_type=%s signals=%s",
            getattr(post, "post_id", "?"),
            _CONTENT_TYPE,
            signals,
        )

        return SignalContext(content_type=_CONTENT_TYPE, signals=signals)