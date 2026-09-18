from __future__ import annotations
import logging
from app.engines.candidate_generator import CandidateGenerator
from app.engines.content_router import ContentRouter, UnsupportedContentTypeError
from app.features.feature_registry import FeatureRegistry
from app.filters.visibility_filter import VisibilityFilter
from app.models.posts import Post
from app.ranking.ranking_engine import RankingEngine
from app.ranking.ranking_input import RankingInput
from app.ranking.ranking_result import RankingResult
from app.retrievers.user_context import UserContext
from app.retrievers.user_context_builder import UserContextBuilder
from app.schemas.feed_schemas import (
    FeatureResultSchema,
    FeedRequest,
    FeedResponse,
    RankedPost,
)
from app.signals.signal_context import SignalContext
from app.visibility.visibility_service import UserPrivacyRepository
from app.repositories.abstract_feed_session_repository import AbstractFeedSessionRepository
from app.repositories.abstract_post_repository import AbstractPostRepository
from redis.exceptions import RedisError

from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class InitialFeedPool:
   
    session_id: str | None
    ranked_results: list[RankingResult]

import app.features  # noqa: F401, E402

logger = logging.getLogger(__name__)

_MVP_CONTENT_TYPES: frozenset[str] = frozenset({"image"})


class UserNotFoundError(Exception):
    """Raised when the requested user_id does not exist in the users table."""

    def __init__(self, user_id: int) -> None:
        self.user_id = user_id
        super().__init__(f"User with id={user_id} does not exist.")

class SessionNotFoundError(Exception):
    def __init__(self, session_id: str) -> None:
        super().__init__(f"Session with id={session_id} not found in Redis.")

class SessionOwnershipError(Exception):
    def __init__(self, session_id: str, user_id: int) -> None:
        super().__init__(f"Session {session_id} does not belong to user_id={user_id}.")

class RedisUnavailableError(Exception):
    """Raised when Redis infrastructure is unavailable or fails."""
    def __init__(self, message: str = "Redis infrastructure is unavailable.") -> None:
        super().__init__(message)


class FeedEngine:
    """
    Orchestrates the full recommendation pipeline for a single user.
    """

    def __init__(
        self,
        candidate_generator: CandidateGenerator,
        ranking_engine: RankingEngine,
        user_context_builder: UserContextBuilder,
        content_router: ContentRouter | None = None,
        feature_registry: type[FeatureRegistry] = FeatureRegistry,
        visibility_filter: VisibilityFilter | None = None,
        user_privacy_repo: UserPrivacyRepository | None = None,
        feed_session_repo: AbstractFeedSessionRepository | None = None,
        post_repo: AbstractPostRepository | None = None,
    ) -> None:
        self._candidate_generator = candidate_generator
        self._ranking_engine      = ranking_engine
        self._user_context_builder = user_context_builder
        self._content_router      = content_router or ContentRouter()
        self._feature_registry    = feature_registry
        self._visibility_filter   = visibility_filter
        self._user_privacy_repo   = user_privacy_repo
        self._feed_session_repo   = feed_session_repo
        self._post_repo           = post_repo

    def _empty_response(self, request: FeedRequest) -> FeedResponse:
        return FeedResponse(
            user_id=request.user_id, 
            session_id=request.session_id, 
            page=request.page,
            limit=request.limit,
            total_returned=0, 
            posts=[]
        )

    def generate_feed(self, request: FeedRequest, is_new_session: bool = False) -> FeedResponse:
       
        logger.info("FeedEngine: starting generation for user=%d", request.user_id)

        self._validate_user_exists(request.user_id)

       
        session_data = None
        if request.session_id and self._feed_session_repo and self._post_repo:
            try:
                session_data = self._feed_session_repo.get_session_page_and_meta(
                    request.session_id, request.page, request.limit
                )
            except RedisError as e:
                logger.error("FeedEngine: Redis feed-session read failure (session/meta): %s", e)
                raise RedisUnavailableError()

        if session_data:
            metadata, post_ids = session_data
            
            if metadata.get("user_id") != str(request.user_id):
                raise SessionOwnershipError(request.session_id, request.user_id)
            if not post_ids:
                return self._empty_response(request)
                
            unsorted_posts = self._post_repo.get_posts_by_ids(post_ids)
            post_map = {p.post_id: p for p in unsorted_posts}
            
            
            ordered_posts = [post_map[pid] for pid in post_ids if pid in post_map]
            
           
            user = self._user_context_builder.build(request.user_id)

            signal_contexts = self._route_signals(ordered_posts)
            ranking_inputs = self._compute_features(user, ordered_posts, signal_contexts)
            
        
            reranked_results = self._ranking_engine.rank(ranking_inputs)
            
           
            reranked_results.sort(key=lambda r: r.score, reverse=True)
            
          
            try:
                self._feed_session_repo.update_scores(request.session_id, reranked_results)
            except RedisError as e:
                logger.error("FeedEngine: Redis feed-session write failure (update_scores): %s", e)
                raise RedisUnavailableError()
            
            
            page_results = []
            for rank_offset, r in enumerate(reranked_results):
                rank = (request.page - 1) * request.limit + rank_offset + 1
                r_updated = RankingResult(post=r.post, score=r.score, rank=rank, feature_breakdown=r.feature_breakdown)
                page_results.append(r_updated)
                
            return self._build_response(request, page_results, ranking_inputs)

       
        if not is_new_session:
            if request.session_id:
                raise SessionNotFoundError(request.session_id)
            
            raise SessionNotFoundError("No session_id provided for existing session request")


        user       = self._user_context_builder.build(request.user_id)
        candidates = self._candidate_generator.generate(request, user)
        if not candidates:
            return self._empty_response(request)

        
        candidates = self._apply_visibility_filter(request.user_id, candidates)
        if not candidates:
            logger.info(
                "FeedEngine: no candidates remain after visibility filter for user=%d",
                request.user_id,
            )
            return self._empty_response(request)

    
        candidates = self._filter_for_mvp(candidates)
        if not candidates:
            logger.info(
                "FeedEngine: no image candidates after MVP filter for user=%d",
                request.user_id,
            )
            return self._empty_response(request)

       
        signal_contexts = self._route_signals(candidates)

    
        ranking_inputs = self._compute_features(user, candidates, signal_contexts)

        ranked_results = self._ranking_engine.rank(ranking_inputs)
        
      
        target_size = self._candidate_generator.target_pool_size
        initial_pool_size = min(target_size, len(ranked_results))
        initial_pool = ranked_results[:initial_pool_size]
        
        if request.session_id and self._feed_session_repo:
            try:
                self._feed_session_repo.save_pool(request.session_id, request.user_id, initial_pool)
            except RedisError as e:
                logger.error("FeedEngine: Redis feed-session write failure (save_pool): %s", e)
                # Best-effort cleanup of partial state
                try:
                    self._feed_session_repo.delete_session(request.session_id)
                except Exception as cleanup_e:
                    logger.warning("FeedEngine: Failed to cleanup partial session %s: %s", request.session_id, cleanup_e)
                raise RedisUnavailableError()
        
      
        start = (request.page - 1) * request.limit
        end = start + request.limit
        page_slice = initial_pool[start:end]

        return self._build_response(request, page_slice, ranking_inputs)


    def _validate_user_exists(self, user_id: int) -> None:
        
        if self._user_privacy_repo is None:
            return
        if not self._user_privacy_repo.exists(user_id):
            logger.warning("FeedEngine: user_id=%d not found — aborting.", user_id)
            raise UserNotFoundError(user_id)

    def _apply_visibility_filter(
        self,
        viewer_id: int,
        candidates: list[Post],
    ) -> list[Post]:
       
        if self._visibility_filter is None:
            return candidates
        return self._visibility_filter.filter(viewer_id=viewer_id, candidates=candidates)

    def _filter_for_mvp(self, candidates: list[Post]) -> list[Post]:
        
        filtered = [
            p for p in candidates
            if (p.content_type or "") in _MVP_CONTENT_TYPES
        ]
        logger.debug(
            "FeedEngine: MVP filter: %d -> %d posts (kept types=%s)",
            len(candidates),
            len(filtered),
            list(_MVP_CONTENT_TYPES),
        )
        return filtered

    def _route_signals(self, candidates: list[Post]) -> dict[int, SignalContext]:
       
        try:
            return self._content_router.route(candidates)
        except UnsupportedContentTypeError:
            logger.exception(
                "FeedEngine: ContentRouter raised UnsupportedContentTypeError. "
                "A post with an unexpected content_type bypassed the MVP filter."
            )
            raise

    def _compute_features(
        self,
        user: UserContext,
        candidates: list[Post],
        signal_contexts: dict[int, SignalContext],
    ) -> list[RankingInput]:
     
        logger.debug("FeedEngine: computing features for %d posts", len(candidates))
        return [
            RankingInput(
                post=post,
                feature_results=self._feature_registry.compute_all(
                    user,
                    post,
                    signal_contexts.get(post.post_id),
                ),
            )
            for post in candidates
        ]

    def _build_response(
        self,
        request: FeedRequest,
        page: list[RankingResult],
        all_inputs: list[RankingInput],
    ) -> FeedResponse:
       
        logger.info(
            "FeedEngine: returning %d posts for user_id=%d",
            len(page),
            request.user_id,
        )
        input_map = {ri.post.post_id: ri.feature_results for ri in all_inputs}
        return FeedResponse(
            user_id=request.user_id,
            session_id=request.session_id,
            page=request.page,
            limit=request.limit,
            total_returned=len(page),
            posts=[self._to_ranked_post(result, input_map) for result in page],
        )

    @staticmethod
    def _to_ranked_post(
        result: RankingResult,
        input_map: dict[int, list],
    ) -> RankedPost:
        """Map a RankingResult to the public RankedPost API schema."""
        post = result.post
        feature_results = input_map.get(post.post_id, [])
        return RankedPost(
            post_id=post.post_id,
            likes=post.likes or 0,
            comments=post.comments or 0,
            shares=post.shares or 0,
            saves=post.saves or 0,
            watch_time=post.watch_time or 0,
            tags=post.tags or [],
            friends=post.friends or 0,
            communities=post.communities or [],
            rank=result.rank,
            relevance_score=result.score,
            feature_breakdown=result.feature_breakdown,
            features=[
                FeatureResultSchema(
                    feature_name=fr.feature_name,
                    score=fr.score,
                    metadata=fr.metadata,
                )
                for fr in feature_results
            ],
        )