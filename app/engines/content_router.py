from __future__ import annotations
import logging
from app.models.posts import Post
from app.signals.image_signals import ImageSignals
from app.signals.signal_context import SignalContext
from app.signals.video_signals import VideoSignals

logger = logging.getLogger(__name__)

class UnsupportedContentTypeError(ValueError):

    def __init__(self, post_id: int | None, content_type: str | None) -> None:
        self.post_id = post_id
        self.content_type = content_type
        super().__init__(
            f"ContentRouter: unsupported content_type={content_type!r} "
            f"for post_id={post_id}.  "
            f"Supported types: {list(_STRATEGY_MAP.keys())}"
        )


_STRATEGY_MAP: dict[str, ImageSignals | VideoSignals] = {
    "image": ImageSignals(),
    "video": VideoSignals(),
}


class ContentRouter:

    def route(self, posts: list[Post]) -> dict[int, SignalContext]:
       
        result: dict[int, SignalContext] = {}

        for post in posts:
            content_type = post.content_type  # may be None

            strategy = _STRATEGY_MAP.get(content_type or "")
            if strategy is None:
                raise UnsupportedContentTypeError(
                    post_id=getattr(post, "post_id", None),
                    content_type=content_type,
                )

            logger.debug(
                "ContentRouter: post_id=%s content_type=%r strategy=%s",
                getattr(post, "post_id", "?"),
                content_type,
                strategy.name,
            )

            result[post.post_id] = strategy.extract(post)

        return result
