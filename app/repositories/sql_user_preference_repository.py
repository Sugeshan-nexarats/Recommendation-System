from __future__ import annotations
import logging
from sqlalchemy import Column, Float, Integer, String
from sqlalchemy.orm import Session, declarative_base
from app.models.preference import Preference
from app.models.user_preference import UserPreference
from app.repositories.abstract_user_preference_repository import (
    AbstractUserPreferenceRepository,
)

logger = logging.getLogger(__name__)
_Base = declarative_base()


class _UserPreferenceRow(_Base):
    
    __tablename__ = "user_preferences"

    user_id: int = Column(Integer, primary_key=True, nullable=False)
    preference_id: int = Column(Integer, primary_key=True, nullable=False)
    preference_weight: float = Column(Float, nullable=False, default=1.0)

class SqlUserPreferenceRepository(AbstractUserPreferenceRepository):

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_user_id(self, user_id: int) -> list[UserPreference]:

        rows = (
            self._db.query(
                _UserPreferenceRow.preference_id,
                Preference.preference_name,
                _UserPreferenceRow.preference_weight,
            )
            .join(
                Preference,
                Preference.preference_id == _UserPreferenceRow.preference_id,
            )
            .filter(_UserPreferenceRow.user_id == user_id)
            .order_by(_UserPreferenceRow.preference_weight.desc())
            .all()
        )

        preferences = [
            UserPreference(
                preference_id=int(row.preference_id),
                preference_name=str(row.preference_name).strip().lower(),
                preference_weight=float(row.preference_weight),
            )
            for row in rows
        ]

        logger.debug(
            "SqlUserPreferenceRepository: user_id=%d → %d preferences loaded: %s",
            user_id,
            len(preferences),
            [p.preference_name for p in preferences],
        )

        return preferences
