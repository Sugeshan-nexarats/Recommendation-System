from __future__ import annotations
from pydantic import BaseModel, Field, model_validator

_DEFAULT_HALF_LIFE_HOURS: float = 24.0  
_DEFAULT_MAX_AGE_HOURS:   float = 168.0 
_DEFAULT_FLOOR_SCORE:     float = 0.0   


class FreshnessConfig(BaseModel):
    
    half_life_hours: float = Field(
        default=_DEFAULT_HALF_LIFE_HOURS,
        gt=0.0,
        description="Age in hours at which freshness score decays to ~50/100.",
    )
    max_age_hours: float = Field(
        default=_DEFAULT_MAX_AGE_HOURS,
        gt=0.0,
        description="Hard staleness gate: posts older than this score floor_score.",
    )
    floor_score: float = Field(
        default=_DEFAULT_FLOOR_SCORE,
        ge=0.0,
        lt=100.0,
        description="Minimum freshness score in [0, 100).  Applied after decay.",
    )

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def max_age_gte_half_life(self) -> "FreshnessConfig":
       
        if self.max_age_hours < self.half_life_hours:
            raise ValueError(
                f"FreshnessConfig: max_age_hours ({self.max_age_hours}) must be "
                f">= half_life_hours ({self.half_life_hours}).  "
                f"A max_age smaller than half_life causes the staleness gate to "
                f"fire before the decay curve has had any meaningful effect."
            )
        return self
