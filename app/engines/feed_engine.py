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
from app.schemas.feed_schemas import (FeatureResultSchema, FeedRequest, FeedResponse, RankedPost,)
from app.signals.signal_context import SignalContext
from app.visibility.visibility_service import UserPrivacyRepository

import app.features  

logger = logging.getLogger(__name__)

CONTENT_TYPES: frozenset[str] = frozenset({"image"})


class UserNotFoundError(Exception):
    """Raised when the requested user_id does not exist in the users table."""

    def __init__(self, user_id: int) -> None:
        self.user_id = user_id
        super().__init__(f"User with id={user_id} does not exist.")


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
    ) -> None:
        self._candidate_generator = candidate_generator
        self._ranking_engine      = ranking_engine
        self._user_context_builder = user_context_builder
        self._content_router      = content_router or ContentRouter()
        self._feature_registry    = feature_registry
        self._visibility_filter   = visibility_filter
        self._user_privacy_repo   = user_privacy_repo

    def generate_feed(self, request: FeedRequest) -> FeedResponse:
       
        logger.info("FeedEngine: starting generation for user=%d", request.user_id)

        self._validate_user_exists(request.user_id)
        user       = self._user_context_builder.build(request.user_id)
        candidates = self._candidate_generator.generate(request, user)
        if not candidates:
            return FeedResponse(user_id=request.user_id, total_returned=0, posts=[])

        candidates = self._apply_visibility_filter(request.user_id, candidates)
        if not candidates:
            logger.info("FeedEngine: no candidates remain after visibility filter for user=%d", request.user_id,)
            return FeedResponse(user_id=request.user_id, total_returned=0, posts=[])

        candidates = self._filter_for_mvp(candidates)
        if not candidates:
            logger.info(
                "FeedEngine: no image candidates after MVP filter for user=%d",
                request.user_id,
            )
            return FeedResponse(user_id=request.user_id, total_returned=0, posts=[])

        signal_contexts = self._route_signals(candidates)
        ranking_inputs = self._compute_features(user, candidates, signal_contexts)
        ranked_results = self._ranking_engine.rank(ranking_inputs)
        page = ranked_results[: request.limit]
        return self._build_response(request, page, ranking_inputs)

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
            if (p.content_type or "") in CONTENT_TYPES
        ]
        logger.debug(
            "FeedEngine: MVP filter: %d -> %d posts (kept types=%s)",
            len(candidates),
            len(filtered),
            list(CONTENT_TYPES),
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

    def _compute_features(self, user: UserContext, candidates: list[Post], signal_contexts: dict[int, SignalContext], 
                          ) -> list[RankingInput]:
       
        logger.debug("FeedEngine: computing features for %d posts", len(candidates))
        return [
            RankingInput(post=post, feature_results=self._feature_registry.compute_all(
                    user,
                    post,
                    signal_contexts.get(post.post_id),
                ),
            )
            for post in candidates
        ]

    def _build_response(self, request: FeedRequest, page: list[RankingResult], all_inputs: list[RankingInput], ) -> FeedResponse:
        
        logger.info(
            "FeedEngine: returning %d posts for user_id=%d",
            len(page),
            request.user_id,
        )
        return FeedResponse(
            user_id=request.user_id,
            total_returned=len(page),
            posts=[self._to_ranked_post(result, all_inputs) for result in page],
        )

    @staticmethod
    def _to_ranked_post(
        result: RankingResult,
        all_inputs: list[RankingInput],
    ) -> RankedPost:
        """Map a RankingResult to the public RankedPost API schema."""
        post = result.post
        feature_results = next((ri.feature_results for ri in all_inputs if ri.post.post_id == post.post_id),[],)
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