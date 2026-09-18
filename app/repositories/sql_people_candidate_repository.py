from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List

from app.repositories.abstract_people_candidate_repository import AbstractPeopleCandidateRepository

class SqlPeopleCandidateRepository(AbstractPeopleCandidateRepository):
  

    def __init__(self, db: Session):
        self._db = db

    def get_candidates_by_shared_interests(self, user_id: int, limit: int = 100) -> List[int]:
     
        query = text("""
            SELECT up2.user_id 
            FROM user_preferences up1
            JOIN user_preferences up2 ON up1.preference_id = up2.preference_id
            WHERE up1.user_id = :user_id 
              AND up2.user_id != :user_id
            GROUP BY up2.user_id
            ORDER BY COUNT(*) DESC
            LIMIT :limit
        """)
        
        result = self._db.execute(query, {"user_id": user_id, "limit": limit}).fetchall()
        return [row[0] for row in result]

    def get_candidates_by_mutual_connections(self, user_id: int, limit: int = 100) -> List[int]:
        """
        Find candidates who are 2nd-degree friends (friends of friends).
        Since FRIEND is bidirectional, we check requester -> target and target -> target.
        For simplicity in this MVP, we will check paths where:
        (user -> friend) AND (friend -> candidate).
        """
        query = text("""
            WITH user_friends AS (
                SELECT target_user_id AS friend_id
                FROM user_relationships
                WHERE requester_user_id = :user_id 
                  AND relationship_type = 'FRIEND' 
                  AND status = 'ACCEPTED'
                UNION
                SELECT requester_user_id AS friend_id
                FROM user_relationships
                WHERE target_user_id = :user_id 
                  AND relationship_type = 'FRIEND' 
                  AND status = 'ACCEPTED'
            ),
            friend_friends AS (
                SELECT r.target_user_id AS candidate_id
                FROM user_relationships r
                JOIN user_friends uf ON r.requester_user_id = uf.friend_id
                WHERE r.relationship_type = 'FRIEND' 
                  AND r.status = 'ACCEPTED'
                  AND r.target_user_id != :user_id
                UNION
                SELECT r.requester_user_id AS candidate_id
                FROM user_relationships r
                JOIN user_friends uf ON r.target_user_id = uf.friend_id
                WHERE r.relationship_type = 'FRIEND' 
                  AND r.status = 'ACCEPTED'
                  AND r.requester_user_id != :user_id
            )
            SELECT candidate_id
            FROM friend_friends
            LIMIT :limit
        """)
        
        result = self._db.execute(query, {"user_id": user_id, "limit": limit}).fetchall()
        return [row[0] for row in result]
