

from __future__ import annotations

from abc import ABC, abstractmethod

from app.models.user_preference import UserPreference


class AbstractUserPreferenceRepository(ABC):
    

    @abstractmethod
    def get_by_user_id(self, user_id: int) -> list[UserPreference]:
       
        ...
