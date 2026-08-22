from __future__ import annotations
import logging
from app.models.posts import Post
from app.repositories.abstract_post_repository import AbstractPostRepository
from app.retrievers.abstract_retriever import AbstractRetriever
from app.retrievers.user_context import UserContext
logger = logging.getLogger(__name__)

class PreferenceRetriever(AbstractRetriever):
    
    def __init__(self, repository: AbstractPostRepository) -> None:
        self._repository = repository

    @property
    def name(self) -> str:
        return "preference_retriever"

    def retrieve(self, user: UserContext, limit: int) -> list[Post]:
        if not user.user_preferences:
            logger.debug(
                "PreferenceRetriever: user_id=%d has no preferences; skipping.",
                user.user_id,
            )
            return []

        preference_tags = [pref.preference_name for pref in user.user_preferences]

        logger.debug(
            "PreferenceRetriever: user_id=%d querying %d preference tags (limit=%d): %s",
            user.user_id,
            len(preference_tags),
            limit,
            preference_tags,
        )

        posts = self._repository.get_posts_by_tags(tags=preference_tags, limit=limit)

        logger.debug(
            "PreferenceRetriever: user_id=%d retrieved %d posts.",
            user.user_id,
            len(posts),
        )

        return posts
