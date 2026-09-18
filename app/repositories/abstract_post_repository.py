

from abc import ABC, abstractmethod
from typing import Optional

from app.models.posts import Post


class AbstractPostRepository(ABC):

    @abstractmethod
    def get_posts_for_user(
        self,
        user_id: int,
        limit: int,
        offset: int,
    ) -> list[Post]:
  
        ...

    @abstractmethod
    def get_post_by_id(self, post_id: int) -> Optional[Post]:
  
        ...

    @abstractmethod
    def get_posts_by_ids(self, post_ids: list[int]) -> list[Post]:
      
        ...

    @abstractmethod
    def get_posts_by_friend_ids(
        self,
        friend_ids: list[int],
        limit: int,
    ) -> list[Post]:
     
        ...

    @abstractmethod
    def get_posts_by_community_ids(
        self,
        community_ids: list[int],
        limit: int,
    ) -> list[Post]:
      
        ...

    @abstractmethod
    def get_recent_posts(self, limit: int) -> list[Post]:
     
        ...

    @abstractmethod
    def get_trending_posts(self, limit: int) -> list[Post]:
      
        ...

    @abstractmethod
    def get_posts_by_tags(
        self,
        tags: list[str],
        limit: int,
    ) -> list[Post]:
    
        ...
