from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class UserPreference:
    
    preference_id: int
    preference_name: str
    preference_weight: float

    def __post_init__(self) -> None:
        if self.preference_weight < 0:
            raise ValueError(
                f"UserPreference.preference_weight must be >= 0, "
                f"got {self.preference_weight!r} for preference_id={self.preference_id!r}."
            )
