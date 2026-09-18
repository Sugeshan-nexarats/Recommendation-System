

from __future__ import annotations

from pydantic import BaseModel, field_validator, model_validator

DEFAULT_WEIGHTS: dict[str, float] = {
    "preference_score":   0.30,
    "interest_overlap":   0.25,
    "relationship_score": 0.20,
    "freshness_score":    0.15,
    "community_score":    0.10,
    "quality_score":      0.07,
    "popularity_score":   0.03,
}


class FeatureWeightConfig(BaseModel):
    

    weights: dict[str, float] = DEFAULT_WEIGHTS

    model_config = {"frozen": True}

    @field_validator("weights")
    @classmethod
    def all_weights_non_negative(cls, v: dict[str, float]) -> dict[str, float]:
        """Reject any negative weight — they would invert feature signals."""
        negatives = {k: w for k, w in v.items() if w < 0.0}
        if negatives:
            raise ValueError(
                f"All feature weights must be >= 0.  "
                f"Negative weights found: {negatives}"
            )
        return v

    @model_validator(mode="after")
    def weights_not_all_zero(self) -> "FeatureWeightConfig":
        """Reject a config where every weight is zero (produces NaN scores)."""
        if all(w == 0.0 for w in self.weights.values()):
            raise ValueError(
                "FeatureWeightConfig: all weights are zero.  "
                "At least one weight must be positive."
            )
        return self

 
    @property
    def normalised_weights(self) -> dict[str, float]:
 
        total = sum(self.weights.values())
        return {k: v / total for k, v in self.weights.items()}

    def weight_for(self, feature_name: str) -> float:
 
        return self.normalised_weights.get(feature_name, 0.0)
