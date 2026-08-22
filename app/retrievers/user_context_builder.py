from __future__ import annotations
import logging
from app.models.user_preference import UserPreference
from app.models.user_relationship import UserRelationship
from app.models.users import PROFILE_VISIBILITY_PUBLIC
from app.repositories.abstract_user_preference_repository import (
    AbstractUserPreferenceRepository,
)
from app.repositories.abstract_user_relationship_repository import (
    AbstractUserRelationshipRepository,
)
from app.repositories.abstract_user_interaction_repository import (
    AbstractUserInteractionRepository,
)
from app.retrievers.user_context import UserContext

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
        }
        try:
            interactions = self._interaction_repo.get_interactions_with_posts_by_user_id(user_id)
            for interaction, post in interactions:
                if not post.tags:
                    continue
                
                tags_list = post.tags if isinstance(post.tags, list) else list(post.tags)
                tags_str = [str(t) for t in tags_list]
                
                itype = interaction.interaction_type
                if itype == "like":
                    result["liked_tags"].extend(tags_str)
                elif itype == "watch":
                    result["watched_tags"].extend(tags_str)
                elif itype == "save":
                    result["saved_tags"].extend(tags_str)
                elif itype in ("comment", "share"):
                    result["interacted_tags"].extend(tags_str)
                    
            return result
        except Exception:
            logger.exception(
                "UserContextBuilder: failed to load interactions for user_id=%d; "
                "defaulting to empty lists.",
                user_id,
            )
            return result
