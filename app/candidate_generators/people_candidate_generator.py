import logging
from typing import Set

from app.repositories.abstract_people_candidate_repository import AbstractPeopleCandidateRepository
from app.repositories.abstract_user_relationship_repository import AbstractUserRelationshipRepository
from app.models.user_relationship import STATUS_ACCEPTED, RELATIONSHIP_TYPE_FRIEND

logger = logging.getLogger(__name__)

class PeopleCandidateGenerator:
    """
    Generates user candidate pools for people recommendations.
    """
    def __init__(
        self,
        candidate_repo: AbstractPeopleCandidateRepository,
        relationship_repo: AbstractUserRelationshipRepository
    ):
        self._candidate_repo = candidate_repo
        self._relationship_repo = relationship_repo

    def generate_candidates(self, user_id: int, pool_size: int = 100) -> Set[int]:
        """
        Fetch a combined set of candidates from various sources and filter out invalid ones.
        """
        candidates: Set[int] = set()

        # 1. Get candidates by mutual connections
        mutual_candidates = self._candidate_repo.get_candidates_by_mutual_connections(user_id, limit=pool_size)
        candidates.update(mutual_candidates)

        # 2. Get candidates by shared interests
        if len(candidates) < pool_size:
            interest_candidates = self._candidate_repo.get_candidates_by_shared_interests(user_id, limit=pool_size)
            candidates.update(interest_candidates)

        # 3. Filtering
        # Exclude self (already excluded in SQL, but just to be safe)
        candidates.discard(user_id)

        if not candidates:
            return set()

        
        relationships = self._relationship_repo.get_relationships_for_visibility(user_id, list(candidates))
        
        excluded_users = set()
        for rel in relationships:
            # We exclude anyone with an existing relationship in either direction.
            # e.g., if they are already friends, or if there is a pending request, or blocked.
            excluded_users.add(rel.requester_user_id)
            excluded_users.add(rel.target_user_id)

        excluded_users.discard(user_id)

        valid_candidates = candidates - excluded_users

        logger.debug(
            "PeopleCandidateGenerator: Generated %d candidates (filtered %d due to existing relationships).",
            len(valid_candidates),
            len(excluded_users)
        )
        return valid_candidates
