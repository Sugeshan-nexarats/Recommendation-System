from __future__ import annotations
import logging
from app.models.posts import Post
from app.repositories.abstract_post_repository import AbstractPostRepository
from app.retrievers.abstract_retriever import AbstractRetriever
from app.retrievers.user_context import UserContext

logger = logging.getLogger(__name__)


class TrendingRetriever(AbstractRetriever):

    def __init__(self, repository: AbstractPostRepository) -> None:
        self._repository = repository

    @property
    def name(self) -> str:
        return "trending_retriever"

    def retrieve(self, user: UserContext, limit: int) -> list[Post]:
      
        logger.debug(
            "TrendingRetriever: fetching top %d trending posts for user_id=%d.",
            limit,
            user.user_id,
        )

        posts = self._repository.get_trending_posts(limit=limit)

        logger.debug(
            "TrendingRetriever: retrieved %d trending posts.",
            len(posts),
        )

        return posts
