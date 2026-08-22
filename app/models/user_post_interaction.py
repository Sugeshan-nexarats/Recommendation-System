from sqlalchemy import Column, Integer, String, DateTime
from app.models.posts import Base

class UserPostInteraction(Base):
    __tablename__ = "user_post_interactions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    post_id = Column(Integer, nullable=False)
    interaction_type = Column(String, nullable=False)
    watch_time = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False)
