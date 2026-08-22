from __future__ import annotations
import logging
from sqlalchemy import Column, DateTime, Integer, String, or_
from sqlalchemy.orm import Session, declarative_base
from app.models.user_relationship import (RELATIONSHIP_TYPE_FRIEND, STATUS_ACCEPTED, UserRelationship, )
from app.repositories.abstract_user_relationship_repository import (AbstractUserRelationshipRepository,)

logger = logging.getLogger(__name__)
_Base = declarative_base()


class _UserRelationshipRow(_Base):

    __tablename__ = "user_relationships"

    id:                int = Column(Integer, primary_key=True, autoincrement=True)
    requester_user_id: int = Column(Integer, nullable=False)
    target_user_id:    int = Column(Integer, nullable=False)
    relationship_type: str = Column(String(32), nullable=False)
    status:            str = Column(String(32), nullable=False)
    created_at             = Column(DateTime, nullable=True)
    updated_at             = Column(DateTime, nullable=True)

def _row_to_domain(row: _UserRelationshipRow) -> UserRelationship:
    """Convert an ORM row to the domain UserRelationship value object."""
    return UserRelationship(
        requester_user_id=int(row.requester_user_id),
        target_user_id=int(row.target_user_id),
        relationship_type=str(row.relationship_type),
        status=str(row.status),
    )

class SqlUserRelationshipRepository(AbstractUserRelationshipRepository):

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_user_id(self, user_id: int) -> list[UserRelationship]:
        
        rows = (
            self._db.query(_UserRelationshipRow)
            .filter(
                _UserRelationshipRow.status == STATUS_ACCEPTED,
                or_(
                    
                    _UserRelationshipRow.requester_user_id == user_id,
                    
                    (
                        (_UserRelationshipRow.target_user_id == user_id)
                        & (_UserRelationshipRow.relationship_type == RELATIONSHIP_TYPE_FRIEND)
                    ),
                ),
            )
            .all()
        )

        relationships = [_row_to_domain(row) for row in rows]

        logger.debug(
            "SqlUserRelationshipRepository.get_by_user_id: user_id=%d → %d relationships",
            user_id,
            len(relationships),
        )

        return relationships

    def get_relationships_for_visibility(
        self,
        viewer_user_id: int,
        creator_user_ids: list[int],
    ) -> list[UserRelationship]:
        if not creator_user_ids:
            return []

        rows = (
            self._db.query(_UserRelationshipRow)
            .filter(
                or_(
                  
                    (
                        (_UserRelationshipRow.requester_user_id == viewer_user_id)
                        & (_UserRelationshipRow.target_user_id.in_(creator_user_ids))
                    ),
                    
                    (
                        (_UserRelationshipRow.target_user_id == viewer_user_id)
                        & (_UserRelationshipRow.requester_user_id.in_(creator_user_ids))
                    ),
                )
            )
            .all()
        )

        relationships = [_row_to_domain(row) for row in rows]

        logger.debug(
            "SqlUserRelationshipRepository.get_relationships_for_visibility: "
            "viewer_id=%d creator_ids=%s → %d rows",
            viewer_user_id,
            creator_user_ids,
            len(relationships),
        )

        return relationships
