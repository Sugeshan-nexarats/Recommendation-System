

from __future__ import annotations

import logging

from app.models.posts import Post
from app.repositories.abstract_post_repository import AbstractPostRepository
from app.retrievers.abstract_retriever import AbstractRetriever
from app.retrievers.user_context import UserContext

logger = logging.getLogger(__name__)


class RecentRetriever(AbstractRetriever):
 

    def __init__(self, repository: AbstractPostRepository) -> None:
        self._repository = repository

    @property
    def name(self) -> str:
        return "recent_retriever"

    def retrieve(self, user: UserContext, limit: int) -> list[Post]:
     
        logger.debug(
            "RecentRetriever: fetching %d recent posts for user_id=%d.",
            limit,
            user.user_id,
        )

        posts = self._repository.get_recent_posts(limit=limit)

        logger.debug(
            "RecentRetriever: retrieved %d recent posts.",
            len(posts),
        )

        return posts
