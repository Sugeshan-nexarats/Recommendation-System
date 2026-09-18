import os
import time
from typing import Optional
from redis import Redis

from app.ranking.ranking_result import RankingResult
from app.repositories.abstract_feed_session_repository import AbstractFeedSessionRepository


class RedisFeedSessionRepository(AbstractFeedSessionRepository):
    """
    Concrete Redis implementation for feed session storage.
    """

    def __init__(self, redis_client: Redis) -> None:
        self._redis = redis_client
        self._ttl_seconds = int(os.getenv("FEED_SESSION_TTL_SECONDS", 7200))

    def save_pool(
        self,
        session_id: str,
        user_id: int,
        ranked_results: list[RankingResult],
    ) -> None:
        if not ranked_results:
            return

        pool_key = f"feed:session:{session_id}:pool"
        scores_key = f"feed:session:{session_id}:scores"
        meta_key = f"feed:session:{session_id}:meta"

        # Ordered list of post IDs
        post_ids = [str(r.post.post_id) for r in ranked_results]
        
        # Hash of post_id -> score
        scores = {str(r.post.post_id): str(r.score) for r in ranked_results}

        # Metadata
        meta = {
            "user_id": str(user_id),
            "pool_size": str(len(ranked_results)),
            "created_at": str(int(time.time()))
        }

        # Execute the writes and TTL commands in a single Redis pipeline
        pipeline = self._redis.pipeline()
        pipeline.rpush(pool_key, *post_ids)
        pipeline.hset(scores_key, mapping=scores)
        pipeline.hset(meta_key, mapping=meta)
        pipeline.expire(pool_key, self._ttl_seconds)
        pipeline.expire(scores_key, self._ttl_seconds)
        pipeline.expire(meta_key, self._ttl_seconds)
        pipeline.execute()

    def get_session_page_and_meta(
        self,
        session_id: str,
        page: int,
        limit: int,
    ) -> tuple[dict[str, str], list[int]] | None:
        pool_key = f"feed:session:{session_id}:pool"
        scores_key = f"feed:session:{session_id}:scores"
        meta_key = f"feed:session:{session_id}:meta"

        start = (page - 1) * limit
        end = start + limit - 1

        pipeline = self._redis.pipeline()
        pipeline.exists(pool_key)
        pipeline.exists(scores_key)
        pipeline.hgetall(meta_key)
        pipeline.lrange(pool_key, start, end)
        pipeline.expire(pool_key, self._ttl_seconds)
        pipeline.expire(scores_key, self._ttl_seconds)
        pipeline.expire(meta_key, self._ttl_seconds)
        results = pipeline.execute()

        pool_exists = results[0]
        scores_exists = results[1]
        meta = results[2]
        post_ids_str = results[3]

        # Strict partial state invalidation: A session is only healthy if ALL three keys exist
        if not (pool_exists and scores_exists and meta):
            return None

        if not post_ids_str:
            # Pool exists but page is empty (requested beyond bounds)
            return meta, []

        post_ids = [int(pid) for pid in post_ids_str]
        return meta, post_ids

    def update_scores(self, session_id: str, ranked_results: list[RankingResult]) -> None:
        if not ranked_results:
            return

        pool_key = f"feed:session:{session_id}:pool"
        scores_key = f"feed:session:{session_id}:scores"
        meta_key = f"feed:session:{session_id}:meta"
        
        # Hash of post_id -> score for ONLY the requested page
        scores = {str(r.post.post_id): str(r.score) for r in ranked_results}

        # Update specific scores and refresh TTL on all keys in a single pipeline
        pipeline = self._redis.pipeline()
        pipeline.hset(scores_key, mapping=scores)
        pipeline.expire(pool_key, self._ttl_seconds)
        pipeline.expire(scores_key, self._ttl_seconds)
        pipeline.expire(meta_key, self._ttl_seconds)
        pipeline.execute()

    def delete_session(self, session_id: str) -> None:
        """Best-effort cleanup of partial session state."""
        pool_key = f"feed:session:{session_id}:pool"
        scores_key = f"feed:session:{session_id}:scores"
        meta_key = f"feed:session:{session_id}:meta"
        
        # Unpipelined delete or pipelined delete. Pipelining is fine.
        pipeline = self._redis.pipeline()
        pipeline.delete(pool_key)
        pipeline.delete(scores_key)
        pipeline.delete(meta_key)
        pipeline.execute()

