from __future__ import annotations
import logging
from app.engines.retrieval_config import RetrievalConfig
from app.models.posts import Post
from app.retrievers.abstract_retriever import AbstractRetriever
from app.retrievers.user_context import UserContext
from app.schemas.feed_schemas import FeedRequest

logger = logging.getLogger(__name__)


class CandidateGenerator:

    def __init__(self, retrievers: list[AbstractRetriever], config: RetrievalConfig | None = None,) -> None:
        if not retrievers:
            raise ValueError(
                "CandidateGenerator requires at least one retriever. "
                "Received an empty list."
            )
        self._retrievers = retrievers
        self._config = config or RetrievalConfig()

    def generate(self, request: FeedRequest, user: UserContext) -> list[Post]:
        
        logger.debug(
            "CandidateGenerator: user_id=%d  retrievers=%s  limits=%s",
            request.user_id,
            [r.name for r in self._retrievers],
            {r.name: self._config.limit_for(r.name) for r in self._retrievers},
        )

        raw_candidates = self._collect(user)
        candidates = self._deduplicate(raw_candidates)

        logger.debug(
            "CandidateGenerator: user_id=%d  raw=%d  unique=%d",
            request.user_id,
            len(raw_candidates),
            len(candidates),
        )
        return candidates

    def _collect(self, user: UserContext) -> list[Post]:
        
        all_posts: list[Post] = []

        for retriever in self._retrievers:
            limit = self._config.limit_for(retriever.name)
            try:
                posts = retriever.retrieve(user, limit)
                all_posts.extend(posts)
                logger.debug(
                    "CandidateGenerator: %s returned %d / %d posts.",
                    retriever.name,
                    len(posts),
                    limit,
                )
            except Exception:  
                logger.exception(
                    "CandidateGenerator: retriever '%s' raised an unexpected "
                    "exception and will be skipped.",
                    retriever.name,
                )

        return all_posts

    @staticmethod
    def _deduplicate(candidates: list[Post]) -> list[Post]:
  
        seen: set[int] = set()
        unique: list[Post] = []
        for post in candidates:
            pid = post.post_id
            if pid not in seen:
                seen.add(pid)
                unique.append(post)
        return unique
