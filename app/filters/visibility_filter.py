
from __future__ import annotations

import logging
from collections import defaultdict

from app.models.posts import Post
from app.models.user_relationship import (
    RELATIONSHIP_TYPE_FRIEND,
    STATUS_ACCEPTED,
    UserRelationship,
)
from app.models.users import PROFILE_VISIBILITY_PRIVATE
from app.repositories.abstract_user_relationship_repository import (
    AbstractUserRelationshipRepository,
)
from app.visibility.visibility_service import UserPrivacyRepository

logger = logging.getLogger(__name__)


class VisibilityFilter:


    def __init__(
        self,
        user_privacy_repo: UserPrivacyRepository,
        relationship_repo: AbstractUserRelationshipRepository,
    ) -> None:
        self._user_privacy_repo = user_privacy_repo
        self._relationship_repo = relationship_repo

    def filter(
        self,
        viewer_id: int,
        candidates: list[Post],
    ) -> list[Post]:

        if not candidates:
            return []

      
        creator_ids: list[int] = list({
            post.creator_id
            for post in candidates
            if post.creator_id is not None
        })

      
        privacy_map: dict[int, str] = self._user_privacy_repo.get_privacy_map(creator_ids)

        
        relationships: list[UserRelationship] = (
            self._relationship_repo.get_relationships_for_visibility(
                viewer_id,
                creator_ids,
            )
        )

        
        rel_index: dict[int, list[UserRelationship]] = defaultdict(list)
        for rel in relationships:
            # Index by the "other" side (the creator, not the viewer).
            if rel.requester_user_id == viewer_id:
                rel_index[rel.target_user_id].append(rel)
            elif rel.target_user_id == viewer_id:
                rel_index[rel.requester_user_id].append(rel)

        
        visible: list[Post] = []
        for post in candidates:
            creator_id = post.creator_id

            
            if creator_id is None:
                visible.append(post)
                continue

            allowed = self._is_allowed(
                viewer_id=viewer_id,
                creator_id=creator_id,
                profile_visibility=privacy_map.get(creator_id, "public"),
                rels=rel_index.get(creator_id, []),
                post=post,
            )
            if allowed:
                visible.append(post)

        logger.debug(
            "VisibilityFilter: viewer=%d  candidates=%d  visible=%d",
            viewer_id,
            len(candidates),
            len(visible),
        )
        return visible


    def _is_allowed(
        self,
        viewer_id: int,
        creator_id: int,
        profile_visibility: str,
        rels: list[UserRelationship],
        post: Post,
    ) -> bool:
  
        
        if profile_visibility != PROFILE_VISIBILITY_PRIVATE:
            logger.debug(
                "VisibilityFilter: viewer_id=%d post_id=%s creator_id=%d "
                "creator_visibility=public visible=True",
                viewer_id,
                getattr(post, "post_id", "?"),
                creator_id,
            )
            return True

      
        has_friend = self._has_accepted_friendship(rels)

        logger.debug(
            "VisibilityFilter: viewer_id=%d post_id=%s creator_id=%d "
            "creator_visibility=private has_friend=%s visible=%s",
            viewer_id,
            getattr(post, "post_id", "?"),
            creator_id,
            has_friend,
            has_friend,
        )
        return has_friend

    @staticmethod
    def _has_accepted_friendship(rels: list[UserRelationship]) -> bool:

        return any(
            rel.relationship_type == RELATIONSHIP_TYPE_FRIEND
            and rel.status == STATUS_ACCEPTED
            for rel in rels
        )
