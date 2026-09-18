import logging
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.recommend_route import get_user_context_builder, get_user_relationship_repository
from app.repositories.sql_people_candidate_repository import SqlPeopleCandidateRepository
from app.candidate_generators.people_candidate_generator import PeopleCandidateGenerator
from app.features.people.abstract_people_feature import AbstractPeopleFeature
from app.features.people.interest_similarity_feature import InterestSimilarityFeature
from app.features.people.mutual_connection_feature import MutualConnectionFeature
from app.ranking.people_weight_config import PeopleWeightConfig
from app.engines.people_engine import PeopleEngine
from app.schemas.people_recommendation import PeopleRequest, PeopleResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["People Recommendations"])

def get_people_candidate_repository(db: Session = Depends(get_db)) -> SqlPeopleCandidateRepository:
    return SqlPeopleCandidateRepository(db)

def get_people_candidate_generator(
    candidate_repo: SqlPeopleCandidateRepository = Depends(get_people_candidate_repository),
    relationship_repo = Depends(get_user_relationship_repository)
) -> PeopleCandidateGenerator:
    return PeopleCandidateGenerator(candidate_repo, relationship_repo)

def get_people_features() -> list[AbstractPeopleFeature]:
    return [
        MutualConnectionFeature(),
        InterestSimilarityFeature()
    ]

def get_people_weight_config() -> PeopleWeightConfig:
    return PeopleWeightConfig()

def get_people_engine(
    candidate_generator: PeopleCandidateGenerator = Depends(get_people_candidate_generator),
    context_builder = Depends(get_user_context_builder),
    features: list[AbstractPeopleFeature] = Depends(get_people_features),
    weight_config: PeopleWeightConfig = Depends(get_people_weight_config)
) -> PeopleEngine:
    return PeopleEngine(
        candidate_generator=candidate_generator,
        context_builder=context_builder,
        features=features,
        weight_config=weight_config
    )

@router.post(
    "/recommend/people",
    response_model=PeopleResponse,
    summary="Generate a personalised people recommendation list."
)
def recommend_people(
    request: PeopleRequest,
    engine: PeopleEngine = Depends(get_people_engine)
) -> PeopleResponse:
    """
    Return a list of people the user may know or want to connect with.
    """
    try:
        return engine.recommend(request)
    except Exception as exc:
        logger.exception("Failed to generate people recommendations")
        raise HTTPException(status_code=500, detail="Internal Server Error") from exc
