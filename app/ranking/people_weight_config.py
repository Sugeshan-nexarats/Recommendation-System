from pydantic import BaseModel, field_validator, model_validator

DEFAULT_PEOPLE_WEIGHTS: dict[str, float] = {
    "mutual_connections": 0.70,
    "interest_similarity": 0.30,
}

class PeopleWeightConfig(BaseModel):

    weights: dict[str, float] = DEFAULT_PEOPLE_WEIGHTS

    model_config = {"frozen": True}

    @field_validator("weights")
    @classmethod
    def all_weights_non_negative(cls, v: dict[str, float]) -> dict[str, float]:
        negatives = {k: w for k, w in v.items() if w < 0.0}
        if negatives:
            raise ValueError(f"All feature weights must be >= 0. Negative weights found: {negatives}")
        return v

    @model_validator(mode="after")
    def weights_not_all_zero(self) -> "PeopleWeightConfig":
        if all(w == 0.0 for w in self.weights.values()):
            raise ValueError("PeopleWeightConfig: all weights are zero. At least one weight must be positive.")
        return self

    @property
    def normalised_weights(self) -> dict[str, float]:
        total = sum(self.weights.values())
        return {k: v / total for k, v in self.weights.items()}

    def weight_for(self, feature_name: str) -> float:
        return self.normalised_weights.get(feature_name, 0.0)
