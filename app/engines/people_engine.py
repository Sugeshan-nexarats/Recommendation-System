import logging
from typing import List, Tuple
from app.schemas.people_recommendation import PeopleRequest, PeopleResponse, PeopleRecommendationItem
from app.candidate_generators.people_candidate_generator import PeopleCandidateGenerator
from app.retrievers.user_context_builder import UserContextBuilder
from app.features.people.abstract_people_feature import AbstractPeopleFeature
from app.ranking.people_weight_config import PeopleWeightConfig

logger = logging.getLogger(__name__)

class PeopleEngine:
    """
    Orchestrates the People Recommendation pipeline.
    """
    def __init__(
        self,
        candidate_generator: PeopleCandidateGenerator,
        context_builder: UserContextBuilder,
        features: List[AbstractPeopleFeature],
        weight_config: PeopleWeightConfig
    ):
        self._candidate_generator = candidate_generator
        self._context_builder = context_builder
        self._features = features
        self._weight_config = weight_config

    def recommend(self, request: PeopleRequest) -> PeopleResponse:
        """
        Generate people recommendations for the given request.
        """
        viewer_context = self._context_builder.build(request.user_id)

      
        pool_size = request.limit * 3
        candidate_ids = self._candidate_generator.generate_candidates(request.user_id, pool_size=pool_size)

        scored_candidates: List[Tuple[float, int, List[str]]] = []

        for cid in candidate_ids:
            try:
                candidate_context = self._context_builder.build(cid)
                
              
                total_score = 0.0
                reasons = []

                for feature in self._features:
                    weight = self._weight_config.weight_for(feature.name)
                    if weight == 0.0:
                        continue
                    
                    result = feature.compute(viewer=viewer_context, candidate=candidate_context)
                    total_score += result.score * weight
                    
                    # Add reason if available and weight > 0
                    if result.score > 0 and "reason_string" in result.metadata:
                        
                        if candidate_context.profile_visibility == "private" and feature.name == "interest_similarity":
                            pass
                        else:
                            reasons.append(result.metadata["reason_string"])
                
                scored_candidates.append((total_score, cid, reasons))
            except Exception:
                logger.exception("Failed to score candidate %d for user %d", cid, request.user_id)
                continue

    
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        
     
        offset = request.cursor if request.cursor else 0
        page = scored_candidates[offset:offset + request.limit]
        
        recommendations = []
        for i, (score, cid, reasons) in enumerate(page):
            recommendations.append(PeopleRecommendationItem(
                recommended_user_id=cid,
                rank=offset + i + 1,
                score=score,
                reasons=reasons
            ))
            
        next_cursor = offset + request.limit if offset + request.limit < len(scored_candidates) else None

        return PeopleResponse(
            user_id=request.user_id,
            total_returned=len(recommendations),
            recommendations=recommendations,
            next_cursor=next_cursor
        )
