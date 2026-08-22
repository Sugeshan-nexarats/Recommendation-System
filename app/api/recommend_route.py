import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.engines.candidate_generator import CandidateGenerator
from app.engines.content_router import ContentRouter
from app.engines.feed_engine import FeedEngine, UserNotFoundError
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
from app.filters.visibility_filter import VisibilityFilter
from app.visibility.visibility_service import UserPrivacyRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["Recommendations"])

def get_post_repository(db: Session = Depends(get_db)) -> SqlPostRepository:

    """Provide a SqlPostRepository bound to the current request's DB session."""

    return SqlPostRepository(db)


def get_preference_retriever(repository: SqlPostRepository = Depends(get_post_repository),) -> PreferenceRetriever:
    
    """Provide a PreferenceRetriever wired to the post repository."""
    
    return PreferenceRetriever(repository)


def get_trending_retriever(repository: SqlPostRepository = Depends(get_post_repository),) -> TrendingRetriever:
    
    """Provide a TrendingRetriever wired to the post repository."""
    
    return TrendingRetriever(repository)


def get_recent_retriever(repository: SqlPostRepository = Depends(get_post_repository),) -> RecentRetriever:
    
    """Provide a RecentRetriever wired to the post repository."""
    
    return RecentRetriever(repository)


def get_retrieval_config() -> RetrievalConfig:
    
    """Provide the active retrieval size configuration."""
    
    return RetrievalConfig()


def get_candidate_generator(
    preference_retriever: PreferenceRetriever = Depends(get_preference_retriever),
    trending_retriever: TrendingRetriever = Depends(get_trending_retriever),
    recent_retriever: RecentRetriever = Depends(get_recent_retriever),
    config: RetrievalConfig = Depends(get_retrieval_config),
) -> CandidateGenerator:
  
    return CandidateGenerator(
        retrievers=[
            preference_retriever,
            trending_retriever,
            recent_retriever,
        ],
        config=config,
    )


def get_weight_config() -> FeatureWeightConfig:
    """Provide the active feature weight configuration."""
    
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


def get_user_preference_repository(db: Session = Depends(get_db),) -> SqlUserPreferenceRepository:
    
    """Provide a SqlUserPreferenceRepository bound to the current request's DB session."""
    
    return SqlUserPreferenceRepository(db)


def get_user_relationship_repository(
    db: Session = Depends(get_db),
) -> SqlUserRelationshipRepository:
   
    """Provide a SqlUserRelationshipRepository bound to the current request's DB session."""
   
    return SqlUserRelationshipRepository(db)


def get_user_interaction_repository(db: Session = Depends(get_db),) -> SqlUserInteractionRepository:
    
    """Provide a SqlUserInteractionRepository bound to the current request's DB session."""
    
    return SqlUserInteractionRepository(db)


def get_user_privacy_repository(db: Session = Depends(get_db),) -> UserPrivacyRepository:
    
    """Provide a UserPrivacyRepository for existence checks and privacy lookups."""
    
    return UserPrivacyRepository(db)


def get_user_context_builder(
    preference_repository: SqlUserPreferenceRepository = Depends(get_user_preference_repository),
    relationship_repository: SqlUserRelationshipRepository = Depends(get_user_relationship_repository),
    interaction_repository: SqlUserInteractionRepository = Depends(get_user_interaction_repository),
    user_privacy_repo: UserPrivacyRepository = Depends(get_user_privacy_repository),
) -> UserContextBuilder:
    
    return UserContextBuilder(
        preference_repository=preference_repository,
        relationship_repository=relationship_repository,
        interaction_repository=interaction_repository,
        user_privacy_repo=user_privacy_repo,
    )


def get_content_router() -> ContentRouter:
    
    """Provide a ContentRouter singleton — stateless, no DB dependency."""
    
    return ContentRouter()


def get_visibility_filter(
    user_privacy_repo: UserPrivacyRepository = Depends(get_user_privacy_repository),
    relationship_repo: SqlUserRelationshipRepository = Depends(get_user_relationship_repository),) -> VisibilityFilter:
    """Provide a VisibilityFilter wired to the privacy and relationship repositories."""
    return VisibilityFilter(
        user_privacy_repo=user_privacy_repo,
        relationship_repo=relationship_repo,
    )


def get_feed_engine(
    candidate_generator: CandidateGenerator = Depends(get_candidate_generator),
    ranking_engine: RankingEngine = Depends(get_ranking_engine),
    user_context_builder: UserContextBuilder = Depends(get_user_context_builder),
    content_router: ContentRouter = Depends(get_content_router),
    visibility_filter: VisibilityFilter = Depends(get_visibility_filter),
    user_privacy_repo: UserPrivacyRepository = Depends(get_user_privacy_repository),
) -> FeedEngine:
    """Provide a FeedEngine wired to all pipeline stages."""
    return FeedEngine(
        candidate_generator=candidate_generator,
        ranking_engine=ranking_engine,
        user_context_builder=user_context_builder,
        content_router=content_router,
        visibility_filter=visibility_filter,
        user_privacy_repo=user_privacy_repo,
    )

@router.get(
    "/recommend/feed",
    response_model=FeedResponse,
    summary="Generate a personalised ranked feed for a user."
)
def recommend_feed(
    user_id: int = Query(..., gt=0, description="ID of the requesting user."),
    limit: int = Query(default=20, ge=1, le=100, description="Page size."),
    offset: int = Query(default=0, ge=0, description="Pagination offset."),
    feed_engine: FeedEngine = Depends(get_feed_engine),
) -> FeedResponse:
    
    request = FeedRequest(user_id=user_id, limit=limit, offset=offset)

    logger.info(
        "recommend_feed: user_id=%d limit=%d offset=%d",
        user_id,
        limit,
        offset,
    )

    try:
        return feed_engine.generate_feed(request)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get(
    "/recommend/feed/backend",
    response_model=RecommendationBackendResponse,
    summary="Generate a personalised ranked feed — minimal backend response.",
)
def recommend_feed_backend(
    user_id: int = Query(..., gt=0, description="ID of the requesting user."),
    limit: int = Query(default=20, ge=1, le=100, description="Page size."),
    offset: int = Query(default=0, ge=0, description="Pagination offset."),
    feed_engine: FeedEngine = Depends(get_feed_engine),
) -> RecommendationBackendResponse:
    
    request = FeedRequest(user_id=user_id, limit=limit, offset=offset)

    logger.info(
        "recommend_feed_backend: user_id=%d limit=%d offset=%d",
        user_id,
        limit,
        offset,
    )

    try:
        detailed: FeedResponse = feed_engine.generate_feed(request)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


    return RecommendationBackendResponse(
        user_id=detailed.user_id,
        recommendations=[
            RecommendationBackendItem(
                post_id=post.post_id,
                rank=post.rank,
                score=post.relevance_score,
            )
            for post in detailed.posts
        ],
    )