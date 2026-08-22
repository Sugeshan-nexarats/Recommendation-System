from __future__ import annotations
import math
from pydantic import BaseModel, Field, field_validator, model_validator

_DEFAULT_WEIGHT_LIKES:      float = 1.0
_DEFAULT_WEIGHT_COMMENTS:   float = 2.0   # comment > like (effort)
_DEFAULT_WEIGHT_SHARES:     float = 3.0   # share = strongest intent
_DEFAULT_WEIGHT_SAVES:      float = 2.5   # save > comment (intent to revisit)
_DEFAULT_WEIGHT_WATCH_TIME: float = 0.8   # passive; lower than likes
_DEFAULT_CAP_LIKES:      float = 10_000.0   # 10k likes → near-maximum signal
_DEFAULT_CAP_COMMENTS:   float = 2_000.0    # 2k comments
_DEFAULT_CAP_SHARES:     float = 1_000.0    # 1k shares
_DEFAULT_CAP_SAVES:      float = 3_000.0    # 3k saves
_DEFAULT_CAP_WATCH_TIME: float = 100_000.0  # 100k seconds aggregate view time

class PopularitySignalWeights(BaseModel):

    likes:      float = Field(default=_DEFAULT_WEIGHT_LIKES,      ge=0.0)
    comments:   float = Field(default=_DEFAULT_WEIGHT_COMMENTS,   ge=0.0)
    shares:     float = Field(default=_DEFAULT_WEIGHT_SHARES,      ge=0.0)
    saves:      float = Field(default=_DEFAULT_WEIGHT_SAVES,       ge=0.0)
    watch_time: float = Field(default=_DEFAULT_WEIGHT_WATCH_TIME,  ge=0.0)

    model_config = {"frozen": True}

class PopularitySignalCaps(BaseModel):
   
    likes:      float = Field(default=_DEFAULT_CAP_LIKES,      gt=0.0)
    comments:   float = Field(default=_DEFAULT_CAP_COMMENTS,   gt=0.0)
    shares:     float = Field(default=_DEFAULT_CAP_SHARES,      gt=0.0)
    saves:      float = Field(default=_DEFAULT_CAP_SAVES,       gt=0.0)
    watch_time: float = Field(default=_DEFAULT_CAP_WATCH_TIME,  gt=0.0)

    model_config = {"frozen": True}

class PopularityWeightConfig(BaseModel):

    weights: PopularitySignalWeights = Field(default_factory=PopularitySignalWeights)
    caps:    PopularitySignalCaps    = Field(default_factory=PopularitySignalCaps)
    model_config = {"frozen": True}

    @model_validator(mode="after")
    def at_least_one_positive_weight(self) -> "PopularityWeightConfig":
       
        if self.total_weight == 0.0:
            raise ValueError(
                "PopularityWeightConfig: all signal weights are zero.  "
                "At least one weight must be > 0."
            )
        return self

    @property
    def total_weight(self) -> float:
        """Sum of all signal weights (used as normalisation denominator)."""
        w = self.weights
        return w.likes + w.comments + w.shares + w.saves + w.watch_time

    def log_normalise(self, value: float, cap: float) -> float:
        """
        Apply log-compression normalisation.
        Formula:log(1 + x) / log(1 + cap)

        """
        if value <= 0.0:
            return 0.0
        log_cap = math.log1p(cap)
        return math.log1p(value) / log_cap
