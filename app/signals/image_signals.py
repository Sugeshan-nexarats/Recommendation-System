
from __future__ import annotations

import logging

from app.models.posts import Post
from app.signals.signal_context import SignalContext

logger = logging.getLogger(__name__)

_CONTENT_TYPE = "image"


class ImageSignals:


    @property
    def name(self) -> str:
        return "ImageSignals"

    def extract(self, post: Post) -> SignalContext:
      
        signals = {
            "likes":      post.likes      or 0,
            "comments":   post.comments   or 0,
            "shares":     post.shares     or 0,
            "saves":      post.saves      or 0,
            "watch_time": post.watch_time or 0,
            "friends":    post.friends    or 0,
        }

        logger.debug(
            "ImageSignals: extracted signals for post_id=%s content_type=%s signals=%s",
            getattr(post, "post_id", "?"),
            _CONTENT_TYPE,
            signals,
        )

        return SignalContext(content_type=_CONTENT_TYPE, signals=signals)
