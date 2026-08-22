from abc import ABC, abstractmethod

from app.models.posts import Post
from app.models.user_post_interaction import UserPostInteraction

class AbstractUserInteractionRepository(ABC):

    @abstractmethod
    def get_interactions_with_posts_by_user_id(self, user_id: int) -> list[tuple[UserPostInteraction, Post]]:
        pass
