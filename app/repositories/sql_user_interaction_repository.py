from sqlalchemy.orm import Session
from app.models.posts import Post
from app.models.user_post_interaction import UserPostInteraction
from app.repositories.abstract_user_interaction_repository import AbstractUserInteractionRepository

class SqlUserInteractionRepository(AbstractUserInteractionRepository):

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_interactions_with_posts_by_user_id(self, user_id: int) -> list[tuple[UserPostInteraction, Post]]:
        """
        Fetch all user interactions joined with posts.
        """
        return (
            self._db.query(UserPostInteraction, Post)
            .join(Post, UserPostInteraction.post_id == Post.post_id)
            .filter(UserPostInteraction.user_id == user_id)
            .all()
        )
