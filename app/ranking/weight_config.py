"""
FeatureWeightConfig — validated, normalised weight map for scoring strategies.

Responsibilities:
    - Provide a type-safe home for the feature→weight mapping.
    - Validate that all weights are non-negative at construction time.
    - Expose normalised weights (sum to 1.0) so every scoring strategy can
      produce a final score that is naturally bounded to [0.0, 1.0] when
      feature scores are already in [0.0, 1.0].
    - Support default weights (uniform) when none are supplied so the engine
      works out-of-the-box in development without any configuration.

Design notes:
    - Weights are stored as-supplied and normalised on first access (lazy,
      cached).  This means the config object is cheap to construct and the
      normalisation overhead is paid exactly once per engine lifetime.
    - The config is immutable after construction (frozen Pydantic model).
      Changing weights requires constructing a new config and injecting a
      new engine — which is the correct production pattern (config reload
      via restart, feature flag swap, or A/B experiment bucket assignment).
"""

from __future__ import annotations

from pydantic import BaseModel, field_validator, model_validator

# Default weights reflecting the relative importance of each feature.
# These are starting values and should be tuned from offline experiments.
DEFAULT_WEIGHTS: dict[str, float] = {
    "preference_score":   0.30,
    "interest_overlap":   0.25,
    "relationship_score": 0.20,
    "freshness_score":    0.15,
    "quality_score":      0.07,
    "popularity_score":   0.03,
}


class FeatureWeightConfig(BaseModel):
    """
    Immutable, validated weight map used by scoring strategies.

    Attributes:
        weights: Mapping of feature_name → raw weight.  All values must be
                 >= 0.  Features not present in this map receive a weight of
                 0.0 (they contribute nothing to the final score).

    Computed property:
        normalised_weights: Same mapping with values scaled so they sum to
                            exactly 1.0.  Used by WeightedSumStrategy.
    """

    weights: dict[str, float] = DEFAULT_WEIGHTS

    model_config = {"frozen": True}

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Computed properties
    # ------------------------------------------------------------------

    @property
    def normalised_weights(self) -> dict[str, float]:
        """
        Return weights scaled to sum to 1.0.

        This guarantees that the weighted dot-product of normalised feature
        scores (all ∈ [0, 1]) and normalised weights also lies in [0, 1].

        Returns:
            A new dict with the same keys and proportionally scaled values.
        """
        total = sum(self.weights.values())
        return {k: v / total for k, v in self.weights.items()}

    def weight_for(self, feature_name: str) -> float:
        """
        Return the normalised weight for a given feature name.

        Unknown features (not in the config) return 0.0 — they are silently
        ignored rather than raising, because new features may be deployed
        before the weight config is updated.

        Args:
            feature_name: Canonical name of the feature (e.g. "interest_overlap").

        Returns:
            Normalised weight in [0.0, 1.0].  Returns 0.0 for unknown features.
        """
        return self.normalised_weights.get(feature_name, 0.0)
