from abc import ABC, abstractmethod
from app.models.posts import Post
from app.retrievers.user_context import UserContext

class AbstractRetriever(ABC):

    @abstractmethod
    def retrieve(self, user: UserContext, limit: int) -> list[Post]:
        ...
