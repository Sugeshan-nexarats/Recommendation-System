from __future__ import annotations
import logging
from sqlalchemy.orm import Session
from app.models.users import PROFILE_VISIBILITY_PUBLIC, Users

logger = logging.getLogger(__name__)


class UserPrivacyRepository:
  

    def __init__(self, db: Session) -> None:
        self._db = db

    def exists(self, user_id: int) -> bool:
       
        return (
            self._db.query(Users.user_id)
            .filter(Users.user_id == user_id)
            .first()
        ) is not None

    def get_profile_visibility(self, user_id: int) -> str:
      
        row = (
            self._db.query(Users.profile_visibility)
            .filter(Users.user_id == user_id)
            .first()
        )
        if row is None:
            return PROFILE_VISIBILITY_PUBLIC
        return str(row.profile_visibility)

    def get_privacy_map(self, user_ids: list[int]) -> dict[int, str]:
        
        if not user_ids:
            return {}

        rows = (
            self._db.query(Users.user_id, Users.profile_visibility)
            .filter(Users.user_id.in_(user_ids))
            .all()
        )

        return {int(row.user_id): str(row.profile_visibility) for row in rows}
