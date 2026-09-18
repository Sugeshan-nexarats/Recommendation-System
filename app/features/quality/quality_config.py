from __future__ import annotations
from pydantic import BaseModel, Field, model_validator

_DEFAULT_WEIGHT_CONTENT:    float = 2.0
_DEFAULT_WEIGHT_SPAM:       float = 3.0
_DEFAULT_WEIGHT_REPUTATION: float = 1.5
_DEFAULT_WEIGHT_REPORTS:    float = 2.5
_DEFAULT_WEIGHT_DUPLICATE:  float = 2.0
_DEFAULT_CAP_REPORTS:       float = 10.0   


class QualitySignalWeights(BaseModel):

    content:    float = Field(default=_DEFAULT_WEIGHT_CONTENT,    ge=0.0)
    spam:       float = Field(default=_DEFAULT_WEIGHT_SPAM,       ge=0.0)
    reputation: float = Field(default=_DEFAULT_WEIGHT_REPUTATION, ge=0.0)
    reports:    float = Field(default=_DEFAULT_WEIGHT_REPORTS,    ge=0.0)
    duplicate:  float = Field(default=_DEFAULT_WEIGHT_DUPLICATE,  ge=0.0)

    model_config = {"frozen": True}


class QualitySignalCaps(BaseModel):
  
    reports: float = Field(default=_DEFAULT_CAP_REPORTS, gt=0.0)

    model_config = {"frozen": True}


class QualityConfig(BaseModel):
  
    weights: QualitySignalWeights = Field(default_factory=QualitySignalWeights)
    caps:    QualitySignalCaps    = Field(default_factory=QualitySignalCaps)

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def at_least_one_positive_weight(self) -> "QualityConfig":
        w = self.weights
        total = w.content + w.spam + w.reputation + w.reports + w.duplicate
        if total == 0.0:
            raise ValueError(
                "QualityConfig: all signal weights are zero. "
                "At least one weight must be > 0."
            )
        return self

    @property
    def total_weight(self) -> float:
        """Sum of all signal weights."""
        w = self.weights
        return w.content + w.spam + w.reputation + w.reports + w.duplicate
