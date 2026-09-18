"""
FastAPI route for the recommendation feed endpoint.

Dependency injection wiring (request scoped):

    HTTP request
        │
        ├─► get_db()                           → SQLAlchemy Session
        │
        ├─► get_post_repository()              → SqlPostRepository(session)
        │
        ├─► get_preference_retriever()         → PreferenceRetriever(post_repo)
        ├─► get_trending_retriever()           → TrendingRetriever(post_repo)
        ├─► get_recent_retriever()             → RecentRetriever(post_repo)
        │
        ├─► get_candidate_generator()          → CandidateGenerator([preference, trending, recent])
        │
        ├─► get_weight_config()                → FeatureWeightConfig
        ├─► get_scoring_strategy()             → WeightedSumStrategy(config)
        ├─► get_ranking_engine()               → RankingEngine(strategy)
        │
        ├─► get_user_preference_repository()   → SqlUserPreferenceRepository(session)
        ├─► get_user_relationship_repository() → SqlUserRelationshipRepository(session)
        ├─► get_user_interaction_repository()  → SqlUserInteractionRepository(session)
        ├─► get_user_privacy_repository()      → UserPrivacyRepository(session)
        ├─► get_user_context_builder()         → UserContextBuilder(pref, rel, interaction, privacy)
        │
        ├─► get_visibility_filter()            → VisibilityFilter(privacy_repo, rel_repo)
        │
        └─► get_feed_engine()                  → FeedEngine(candidate_generator,
                                                             ranking_engine,
                                                             user_context_builder,
                                                             visibility_filter,
                                                             user_privacy_repo)

All dependencies are assembled at this boundary — not inside engine classes —
keeping the entire core pipeline fully framework-agnostic.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Header
import os
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.engines.candidate_generator import CandidateGenerator
from app.engines.content_router import ContentRouter
from app.engines.feed_engine import FeedEngine, UserNotFoundError, SessionNotFoundError, SessionOwnershipError, RedisUnavailableError
from app.engines.retrieval_config import RetrievalConfig
from app.ranking.ranking_engine import RankingEngine
from app.ranking.weight_config import FeatureWeightConfig
from app.ranking.weighted_sum_strategy import WeightedSumStrategy
from app.repositories.sql_post_repository import SqlPostRepository
from app.repositories.sql_user_preference_repository import SqlUserPreferenceRepository
from app.repositories.sql_user_relationship_repository import SqlUserRelationshipRepository
from app.repositories.sql_user_interaction_repository import SqlUserInteractionRepository
from app.retrievers.preference_retriever import PreferenceRetriever
from app.retrievers.recent_retriever import RecentRetriever
from app.retrievers.trending_retriever import TrendingRetriever
from app.retrievers.user_context_builder import UserContextBuilder
from app.schemas.feed_schemas import (
    FeedRequest,
    FeedResponse,
    RecommendationBackendItem,
    RecommendationBackendResponse,
)
from app.schemas.interaction_schemas import InteractionRequest, InteractionResponse
from app.models.user_post_interaction import UserPostInteraction
from datetime import datetime
from app.filters.visibility_filter import VisibilityFilter
from app.visibility.visibility_service import UserPrivacyRepository
from app.sessions.abstract_session_provider import AbstractSessionProvider
from app.sessions.dev_session_provider import DevSessionProvider
from app.sessions.production_session_provider import ProductionSessionProvider
from app.db.redis import get_redis_client
from app.repositories.redis_feed_session_repository import RedisFeedSessionRepository
from app.repositories.redis_user_interaction_repository import RedisUserInteractionRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Recommendations"])


# ---------------------------------------------------------------------------
# Dependency providers
# ---------------------------------------------------------------------------

_dev_session_provider = DevSessionProvider()
_prod_session_provider = ProductionSessionProvider()

def get_session_provider() -> AbstractSessionProvider:
    """
    Provide the active SessionProvider based on environment.
    """
    if os.getenv("ENV") == "production":
        return _prod_session_provider
    return _dev_session_provider

def get_post_repository(db: Session = Depends(get_db)) -> SqlPostRepository:
    """Provide a SqlPostRepository bound to the current request's DB session."""
    return SqlPostRepository(db)


def get_preference_retriever(
    repository: SqlPostRepository = Depends(get_post_repository),
) -> PreferenceRetriever:
    """Provide a PreferenceRetriever wired to the post repository."""
    return PreferenceRetriever(repository)


def get_trending_retriever(
    repository: SqlPostRepository = Depends(get_post_repository),
) -> TrendingRetriever:
    """Provide a TrendingRetriever wired to the post repository."""
    return TrendingRetriever(repository)


def get_recent_retriever(
    repository: SqlPostRepository = Depends(get_post_repository),
) -> RecentRetriever:
    """Provide a RecentRetriever wired to the post repository."""
    return RecentRetriever(repository)


def get_retrieval_config() -> RetrievalConfig:
    """
    Provide the active retrieval size configuration.

    In production, load values from environment variables or a feature-flag
    service instead of using the class defaults.  Isolating it here means
    the injection point changes without touching CandidateGenerator.
    """
    return RetrievalConfig()


def get_candidate_generator(
    preference_retriever: PreferenceRetriever = Depends(get_preference_retriever),
    trending_retriever: TrendingRetriever = Depends(get_trending_retriever),
    recent_retriever: RecentRetriever = Depends(get_recent_retriever),
    config: RetrievalConfig = Depends(get_retrieval_config),
) -> CandidateGenerator:
    """
    Provide a CandidateGenerator wired to all active retrieval sources.

    Retriever order determines deduplication priority (first-occurrence wins).
    Preference posts are prioritised over trending and recent posts.
    """
    return CandidateGenerator(
        retrievers=[
            preference_retriever,
            trending_retriever,
            recent_retriever,
        ],
        config=config,
    )


def get_weight_config() -> FeatureWeightConfig:
    """
    Provide the active feature weight configuration.

    In production this would be loaded from a config store (e.g. environment
    variables, a feature-flag service, or an A/B experiment bucket) rather
    than using the module-level defaults.  Isolating it here means the
    injection point changes without touching any engine code.
    """
    return FeatureWeightConfig()


def get_scoring_strategy(
    config: FeatureWeightConfig = Depends(get_weight_config),
) -> WeightedSumStrategy:
    """Provide a WeightedSumStrategy configured with the active weight config."""
    return WeightedSumStrategy(config=config)


def get_ranking_engine(
    strategy: WeightedSumStrategy = Depends(get_scoring_strategy),
) -> RankingEngine:
    """Provide a RankingEngine wired to the active scoring strategy."""
    return RankingEngine(strategy=strategy)


def get_user_preference_repository(
    db: Session = Depends(get_db),
) -> SqlUserPreferenceRepository:
    """Provide a SqlUserPreferenceRepository bound to the current request's DB session."""
    return SqlUserPreferenceRepository(db)


def get_user_relationship_repository(
    db: Session = Depends(get_db),
) -> SqlUserRelationshipRepository:
    """Provide a SqlUserRelationshipRepository bound to the current request's DB session."""
    return SqlUserRelationshipRepository(db)


def get_user_interaction_repository(
    db: Session = Depends(get_db),
) -> SqlUserInteractionRepository:
    """Provide a SqlUserInteractionRepository bound to the current request's DB session."""
    return SqlUserInteractionRepository(db)


def get_sql_user_interaction_repository(
    db: Session = Depends(get_db),
) -> SqlUserInteractionRepository:
    """Provide a concrete SqlUserInteractionRepository."""
    return SqlUserInteractionRepository(db)


def get_user_privacy_repository(
    db: Session = Depends(get_db),
) -> UserPrivacyRepository:
    """Provide a UserPrivacyRepository for existence checks and privacy lookups."""
    return UserPrivacyRepository(db)

def get_redis_user_interaction_repository() -> RedisUserInteractionRepository:
    """Provide a RedisUserInteractionRepository connected to the global Redis client."""
    return RedisUserInteractionRepository(get_redis_client())

def get_user_context_builder(
    preference_repository: SqlUserPreferenceRepository = Depends(
        get_user_preference_repository
    ),
    relationship_repository: SqlUserRelationshipRepository = Depends(
        get_user_relationship_repository
    ),
    interaction_repository: SqlUserInteractionRepository = Depends(
        get_user_interaction_repository
    ),
    user_privacy_repo: UserPrivacyRepository = Depends(get_user_privacy_repository),
    redis_interaction_repo: RedisUserInteractionRepository = Depends(
        get_redis_user_interaction_repository
    ),
) -> UserContextBuilder:
    """Provide a UserContextBuilder wired to all data repositories.

    The user_privacy_repo enables UserContextBuilder to load the viewer's own
    profile_visibility when constructing UserContext.
    """
    return UserContextBuilder(
        preference_repository=preference_repository,
        relationship_repository=relationship_repository,
        interaction_repository=interaction_repository,
        user_privacy_repo=user_privacy_repo,
        redis_interaction_repo=redis_interaction_repo,
    )


def get_content_router() -> ContentRouter:
    """Provide a ContentRouter singleton — stateless, no DB dependency."""
    return ContentRouter()


def get_visibility_filter(
    user_privacy_repo: UserPrivacyRepository = Depends(get_user_privacy_repository),
    relationship_repo: SqlUserRelationshipRepository = Depends(
        get_user_relationship_repository
    ),
) -> VisibilityFilter:
    """Provide a VisibilityFilter wired to the privacy and relationship repositories."""
    return VisibilityFilter(
        user_privacy_repo=user_privacy_repo,
        relationship_repo=relationship_repo,
    )


def get_redis_feed_session_repository() -> RedisFeedSessionRepository:
    """Provide a RedisFeedSessionRepository connected to the global Redis client."""
    return RedisFeedSessionRepository(get_redis_client())


def get_feed_engine(
    candidate_generator: CandidateGenerator = Depends(get_candidate_generator),
    ranking_engine: RankingEngine = Depends(get_ranking_engine),
    user_context_builder: UserContextBuilder = Depends(get_user_context_builder),
    content_router: ContentRouter = Depends(get_content_router),
    visibility_filter: VisibilityFilter = Depends(get_visibility_filter),
    user_privacy_repo: UserPrivacyRepository = Depends(get_user_privacy_repository),
    feed_session_repo: RedisFeedSessionRepository = Depends(get_redis_feed_session_repository),
    post_repo: SqlPostRepository = Depends(get_post_repository),
) -> FeedEngine:
    """Provide a FeedEngine wired to all pipeline stages."""
    return FeedEngine(
        candidate_generator=candidate_generator,
        ranking_engine=ranking_engine,
        user_context_builder=user_context_builder,
        content_router=content_router,
        visibility_filter=visibility_filter,
        user_privacy_repo=user_privacy_repo,
        feed_session_repo=feed_session_repo,
        post_repo=post_repo,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/recommend/feed",
    response_model=FeedResponse,
    summary="Generate a personalised ranked feed for a user."
)
def recommend_feed(
    user_id: int = Query(..., gt=0, description="ID of the requesting user."),
    limit: int = Query(default=20, ge=1, le=100, description="Page size."),
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)."),
    session_id: str | None = Query(default=None, description="Client-provided session ID."),
    x_feed_session_new: str = Header(default="false", description="Lifecycle signal: true if Java created a new session."),
    session_provider: AbstractSessionProvider = Depends(get_session_provider),
    feed_engine: FeedEngine = Depends(get_feed_engine),
) -> FeedResponse:
    """
    Return a personalised, ranked feed of posts for the given user.

    Each post in the response includes:
      - relevance_score  — final weighted score ∈ [0, 1].
      - rank             — 1-indexed position (rank=1 = most relevant).
      - feature_breakdown — per-feature weighted contributions.
      - features         — raw feature signals from Stage 3.

    Returns 404 if the user_id does not exist.
    """
    is_new_session_bool = x_feed_session_new.lower() == "true"
    actual_session_id, is_newly_created = session_provider.get_session_id(
        user_id=user_id,
        provided_session_id=session_id,
        is_new_session=is_new_session_bool
    )

    request = FeedRequest(
        user_id=user_id, 
        limit=limit, 
        page=page, 
        session_id=actual_session_id
    )

    logger.info(
        "recommend_feed: user_id=%d limit=%d page=%d session_id=%s is_newly_created=%s",
        user_id,
        limit,
        page,
        actual_session_id,
        is_newly_created,
    )

    try:
        return feed_engine.generate_feed(request, is_new_session=is_newly_created)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SessionOwnershipError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except RedisUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get(
    "/recommend/feed/backend",
    response_model=RecommendationBackendResponse,
    summary="Generate a personalised ranked feed — minimal backend response.",
)
def recommend_feed_backend(
    user_id: int = Query(..., gt=0, description="ID of the requesting user."),
    limit: int = Query(default=20, ge=1, le=100, description="Page size."),
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)."),
    session_id: str | None = Query(default=None, description="Client-provided session ID."),
    x_feed_session_new: str = Header(default="false", description="Lifecycle signal: true if Java created a new session."),
    session_provider: AbstractSessionProvider = Depends(get_session_provider),
    feed_engine: FeedEngine = Depends(get_feed_engine),
) -> RecommendationBackendResponse:
    """
    Return a personalised, ranked feed of posts for the given user.

    This endpoint uses the SAME FeedEngine, CandidateGenerator, and
    RankingEngine as GET /api/v1/recommend/feed.  The only difference is
    the response shape: only post_id, rank, and score are returned.

    Intended for backend-to-backend consumption where a minimal payload
    is preferred over the full feature-diagnostic response.

    Returns 404 if the user_id does not exist.
    """
    is_new_session_bool = x_feed_session_new.lower() == "true"
    actual_session_id, is_newly_created = session_provider.get_session_id(
        user_id=user_id,
        provided_session_id=session_id,
        is_new_session=is_new_session_bool
    )

    request = FeedRequest(
        user_id=user_id, 
        limit=limit, 
        page=page, 
        session_id=actual_session_id
    )

    logger.info(
        "recommend_feed_backend: user_id=%d limit=%d page=%d session_id=%s is_newly_created=%s",
        user_id,
        limit,
        page,
        actual_session_id,
        is_newly_created,
    )

    try:
        # Run the full recommendation pipeline (identical to the test endpoint).
        detailed: FeedResponse = feed_engine.generate_feed(request, is_new_session=is_newly_created)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SessionOwnershipError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except RedisUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    # Map the already-ranked posts to the minimal backend schema.
    # post.rank and post.relevance_score come directly from RankingResult —
    # no re-ranking or re-scoring is performed here.
    return RecommendationBackendResponse(
        user_id=detailed.user_id,
        session_id=detailed.session_id,
        page=page,
        limit=limit,
        recommendations=[
            RecommendationBackendItem(
                post_id=post.post_id,
                rank=post.rank,
                score=post.relevance_score,
            )
            for post in detailed.posts
        ],
    )

@router.post(
    "/recommend/interaction", 
    response_model=InteractionResponse,
    summary="Record a user-post interaction for future feed recommendations."
)
def record_interaction(
    request: InteractionRequest,
    interaction_repo: SqlUserInteractionRepository = Depends(get_sql_user_interaction_repository),
    post_repo: SqlPostRepository = Depends(get_post_repository),
    redis_interaction_repo: RedisUserInteractionRepository = Depends(get_redis_user_interaction_repository)
) -> InteractionResponse:
    """
    Record a user-post interaction (Phase 7 & 8).
    
    This interaction is durably saved to the PostgreSQL database.
    After successful durable storage, a derived recommendation state 
    is pushed to Redis.
    """
    try:
        interaction = UserPostInteraction(
            user_id=request.user_id,
            post_id=request.post_id,
            interaction_type=request.interaction_type,
            watch_time=request.watch_time,
            created_at=datetime.utcnow()
        )
        # 1. Durable write to PostgreSQL (Source of Truth)
        interaction_repo.save_interaction(interaction)
    except Exception as e:
        logger.exception("Failed to record interaction in PostgreSQL: %s", e)
        raise HTTPException(
            status_code=500,
            detail="An internal server error occurred while saving the interaction."
        )

    # 2. Update Redis Derived State
    try:
        post = post_repo.get_post_by_id(request.post_id)
        if post:
            # Safely cast tags and communities to list if they aren't None
            tags = list(post.tags) if post.tags else []
            communities = list(post.communities) if post.communities else []
            
            redis_interaction_repo.update_derived_state(
                user_id=request.user_id,
                post_id=request.post_id,
                interaction_type=request.interaction_type,
                tags=tags,
                communities=communities
            )
        else:
            logger.warning("Post %d not found; cannot update Redis derived interaction state for user %d.", request.post_id, request.user_id)
    except Exception as e:
        # Swallow Redis or Post lookup exceptions to ensure the HTTP response remains successful
        # since the durable interaction was successfully saved in Postgres.
        logger.exception("Failed to update Redis derived state for user %d (interaction saved durably): %s", request.user_id, e)

    return InteractionResponse(message="Interaction successfully recorded.")