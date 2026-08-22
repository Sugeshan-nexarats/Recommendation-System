from __future__ import annotations
from abc import ABC, abstractmethod
from app.models.user_relationship import UserRelationship

class AbstractUserRelationshipRepository(ABC):

    @abstractmethod
    def get_by_user_id(self, user_id: int) -> list[UserRelationship]:
        ...

    @abstractmethod
    def get_relationships_for_visibility(
        self,
        viewer_user_id: int,
        creator_user_ids: list[int],
    ) -> list[UserRelationship]:
        
        ...
