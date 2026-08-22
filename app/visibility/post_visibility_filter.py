from __future__ import annotations
import logging
from collections import defaultdict
from app.models.posts import Post
from app.models.user_relationship import (
    RELATIONSHIP_TYPE_BLOCK,
    RELATIONSHIP_TYPE_FRIEND,
    STATUS_ACCEPTED,
    UserRelationship,
)
from app.repositories.abstract_user_relationship_repository import (
    AbstractUserRelationshipRepository,
)
from app.visibility.visibility_service import UserPrivacyRepository

logger = logging.getLogger(__name__)


class PostVisibilityFilter:
    
    def __init__(
        self,
        user_privacy_repo: UserPrivacyRepository,
        relationship_repo: AbstractUserRelationshipRepository,
    ) -> None:
        self._user_privacy_repo = user_privacy_repo
        self._relationship_repo = relationship_repo

    def filter_posts(
        self,
        viewer_user_id: int,
        posts: list[Post],
    ) -> list[Post]:
        if not posts:
            return []
        creator_ids: list[int] = list({
            post.creator_id
            for post in posts
            if post.creator_id is not None
        })
        privacy_map: dict[int, str] = self._user_privacy_repo.get_privacy_map(creator_ids)
        relationships: list[UserRelationship] = (
            self._relationship_repo.get_relationships_for_visibility(
                viewer_user_id,
                creator_ids,
            )
        )
        rel_index: dict[int, list[UserRelationship]] = defaultdict(list)
        for rel in relationships:
            # Index by the creator's side (the "other" user from the viewer)
            if rel.requester_user_id == viewer_user_id:
                rel_index[rel.target_user_id].append(rel)
            else:
                rel_index[rel.requester_user_id].append(rel)

       
        visible: list[Post] = []
        for post in posts:
            creator_id = post.creator_id

           
            if creator_id is None:
                visible.append(post)
                continue

            creator_rels = rel_index.get(creator_id, [])

            if self._is_blocked(viewer_user_id, creator_id, creator_rels):
                logger.debug(
                    "PostVisibilityFilter: BLOCK — post_id=%s creator_id=%s viewer=%s",
                    post.post_id, creator_id, viewer_user_id,
                )
                continue

            # Default to "public" when creator row is missing (degrade safely)
            profile_visibility = privacy_map.get(creator_id, "public")

            if profile_visibility != "private":
             
                visible.append(post)
                continue

           
            if self._has_accepted_friendship(viewer_user_id, creator_id, creator_rels):
                visible.append(post)
            else:
                logger.debug(
                    "PostVisibilityFilter: PRIVATE creator with no accepted friendship "
                    "— post_id=%s creator_id=%s viewer=%s",
                    post.post_id, creator_id, viewer_user_id,
                )

        logger.debug(
            "PostVisibilityFilter: viewer=%d  in=%d  visible=%d",
            viewer_user_id, len(posts), len(visible),
        )
        return visible

    @staticmethod
    def _is_blocked(
        viewer_id: int,
        creator_id: int,
        rels: list[UserRelationship],
    ) -> bool:
      
        for rel in rels:
            if rel.relationship_type == RELATIONSHIP_TYPE_BLOCK:
                return True
        return False

    @staticmethod
    def _has_accepted_friendship(
        viewer_id: int,
        creator_id: int,
        rels: list[UserRelationship],
    ) -> bool:
       
        for rel in rels:
            if (
                rel.relationship_type == RELATIONSHIP_TYPE_FRIEND
                and rel.status == STATUS_ACCEPTED
            ):
                return True
        return False
