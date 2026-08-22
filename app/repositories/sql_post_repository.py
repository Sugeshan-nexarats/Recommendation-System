from typing import Optional
from sqlalchemy.orm import Session
from app.models.posts import Post
from app.repositories.abstract_post_repository import AbstractPostRepository


class SqlPostRepository(AbstractPostRepository):

    def __init__(self, db: Session) -> None:
        self._db = db


    def get_posts_for_user(self,user_id: int,limit: int,offset: int,) -> list[Post]:
       
        return (
            self._db.query(Post)
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_post_by_id(self, post_id: int) -> Optional[Post]:
        return self._db.query(Post).filter(Post.post_id == post_id).first()

    def get_posts_by_friend_ids(
        self,
        friend_ids: list[int],
        limit: int,
    ) -> list[Post]:
       
        if not friend_ids:
            return []
            
        return (
            self._db.query(Post)
            .filter(Post.friends > 0)
            .order_by(Post.friends.desc())
            .limit(limit)
            .all()
        )

    def get_posts_by_community_ids(
        self,
        community_ids: list[int],
        limit: int,
    ) -> list[Post]:
       
        from sqlalchemy import String, cast, or_
        
        if not community_ids:
            return []
            
        conditions = [cast(Post.communities, String).like(f'%{c}%') for c in community_ids]
        
        return (
            self._db.query(Post)
            .filter(or_(*conditions))
            .limit(limit)
            .all()
        )

    def get_recent_posts(self, limit: int) -> list[Post]:
       
        return (
            self._db.query(Post)
            .order_by(Post.post_id.desc())
            .limit(limit)
            .all()
        )

    def get_trending_posts(self, limit: int) -> list[Post]:
        
        return (
            self._db.query(Post)
            .order_by((Post.likes + Post.comments + Post.shares + Post.saves).desc())
            .limit(limit)
            .all()
        )

    def get_posts_by_tags(
        self,
        tags: list[str],
        limit: int,
    ) -> list[Post]:
       
        from sqlalchemy import String, cast, or_
        
        if not tags:
            return []
            
       
        conditions = [cast(Post.tags, String).like(f'%"{t}"%') for t in tags]
        
        return (
            self._db.query(Post)
            .filter(or_(*conditions))
            .limit(limit)
            .all()
        )
