from __future__ import annotations
import logging
from app.models.user_preference import UserPreference
from app.models.user_relationship import UserRelationship
from app.models.users import PROFILE_VISIBILITY_PUBLIC
from app.repositories.abstract_user_preference_repository import (AbstractUserPreferenceRepository,)
from app.repositories.abstract_user_relationship_repository import (AbstractUserRelationshipRepository,)
from app.repositories.abstract_user_interaction_repository import (AbstractUserInteractionRepository,)
from app.retrievers.user_context import UserContext
from app.models.interaction_weights import get_weight_for_interaction_type

logger = logging.getLogger(__name__)

class UserContextBuilder:
    
    def __init__(
        self,
        preference_repository: AbstractUserPreferenceRepository,
        relationship_repository: AbstractUserRelationshipRepository,
        interaction_repository: AbstractUserInteractionRepository,
        user_privacy_repo=None,  # UserPrivacyRepository | None
    ) -> None:
        self._preference_repo    = preference_repository
        self._relationship_repo  = relationship_repository
        self._interaction_repo   = interaction_repository
        self._user_privacy_repo  = user_privacy_repo

    def build(self, user_id: int) -> UserContext:
        profile_visibility = self._load_profile_visibility(user_id)
        preferences        = self._load_preferences(user_id)
        relationships      = self._load_relationships(user_id)
        interaction_data   = self._load_interactions(user_id)

        logger.debug(
            "UserContextBuilder: user_id=%d built context with "
            "%d preferences, %d relationships, profile_visibility=%s",
            user_id,
            len(preferences),
            len(relationships),
            profile_visibility,
        )

        return UserContext(
            user_id=user_id,
            profile_visibility=profile_visibility,
            user_preferences=tuple(preferences),
            user_relationships=tuple(relationships),
            liked_tags=interaction_data["liked_tags"],
            watched_tags=interaction_data["watched_tags"],
            saved_tags=interaction_data["saved_tags"],
            interacted_tags=interaction_data["interacted_tags"],
            community_affinity=interaction_data["community_affinity"],
        )

    def _load_profile_visibility(self, user_id: int) -> str:

        if self._user_privacy_repo is None:
            return PROFILE_VISIBILITY_PUBLIC
        try:
            return self._user_privacy_repo.get_profile_visibility(user_id)
        except Exception:
            logger.exception(
                "UserContextBuilder: failed to load profile_visibility for user_id=%d; "
                "defaulting to 'public'.",
                user_id,
            )
            return PROFILE_VISIBILITY_PUBLIC

    def _load_preferences(self, user_id: int) -> list[UserPreference]:
        try:
            return self._preference_repo.get_by_user_id(user_id)
        except Exception:
            logger.exception(
                "UserContextBuilder: failed to load preferences for user_id=%d; "
                "defaulting to empty list.",
                user_id,
            )
            return []

    def _load_relationships(self, user_id: int) -> list[UserRelationship]:

        try:
            return self._relationship_repo.get_by_user_id(user_id)
        except Exception:
            logger.exception(
                "UserContextBuilder: failed to load relationships for user_id=%d; "
                "defaulting to empty list.",
                user_id,
            )
            return []

    def _load_interactions(self, user_id: int) -> dict[str, list[str]]:
        result = {
            "liked_tags": [],
            "watched_tags": [],
            "saved_tags": [],
            "interacted_tags": [],
            "community_affinity": {},
        }
        try:
            interactions = self._interaction_repo.get_interactions_with_posts_by_user_id(user_id)
            for interaction, post in interactions:
                itype = interaction.interaction_type
                
                if post.tags:
                    tags_list = post.tags if isinstance(post.tags, list) else list(post.tags)
                    tags_str = [str(t) for t in tags_list]
                    
                    if itype == "like":
                        result["liked_tags"].extend(tags_str)
                    elif itype == "watch":
                        result["watched_tags"].extend(tags_str)
                    elif itype == "save":
                        result["saved_tags"].extend(tags_str)
                    elif itype in ("comment", "share"):
                        result["interacted_tags"].extend(tags_str)
                
                if post.communities:
                    comm_list = post.communities if isinstance(post.communities, list) else list(post.communities)
                    unique_communities = {str(c).strip() for c in comm_list if str(c).strip()}
                    if unique_communities:
                        weight = get_weight_for_interaction_type(itype)
                        for comm in unique_communities:
                            result["community_affinity"][comm] = result["community_affinity"].get(comm, 0.0) + weight
            logger.info(
                "Community affinity for user_id=%d: %s",
                user_id,
                result["community_affinity"],
            )

         
            return result
        except Exception:
            logger.exception(
                "UserContextBuilder: failed to load interactions for user_id=%d; "
                "defaulting to empty lists.",
                user_id,
            )
            return result

            
