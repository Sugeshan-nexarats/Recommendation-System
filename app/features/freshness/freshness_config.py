"""
FreshnessConfig — injectable, validated configuration for FreshnessFeature.

Every numeric constant, time boundary, and behavioural switch used by the
freshness algorithm lives here.  Nothing is hardcoded in feature logic.

Configuration axes:
    1. Decay parameters  — half_life_hours, max_age_hours, floor_score
    2. Decay function    — which mathematical curve to apply (injected strategy)
    3. Age provider      — how to extract post age (injected strategy)

Default calibration:
    half_life_hours = 24   A post at 24 h old scores ~50% on exponential decay.
                           Tune upward for slower-moving communities (e.g. long-
                           form essay platforms), downward for real-time feeds.
    max_age_hours   = 168  Posts older than 7 days receive the floor_score.
                           This is a hard upper bound, not part of the decay curve.
    floor_score     = 0.0  Minimum freshness score.  Set > 0 to ensure old-but-
                           evergreen content is never completely excluded.

All values are validated at construction time.  Invalid configs raise at
startup, not silently mid-request.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

# ---------------------------------------------------------------------------
# Default calibration constants (documented as named values, not literals)
# ---------------------------------------------------------------------------

_DEFAULT_HALF_LIFE_HOURS: float = 24.0   # age at which score ≈ 50 on exp decay
_DEFAULT_MAX_AGE_HOURS:   float = 168.0  # 7 days — hard staleness cutoff
_DEFAULT_FLOOR_SCORE:     float = 0.0    # minimum possible freshness [0, 100)


class FreshnessConfig(BaseModel):
    """
    Complete, immutable configuration for FreshnessFeature.

    Attributes:
        half_life_hours: The post age (in hours) at which the exponential
                         decay function returns 0.5 (50 out of 100).
                         Also used as the boundary in linear and step decay.
                         Must be strictly positive.
        max_age_hours:   Posts older than this receive floor_score.
                         Acts as a hard staleness gate applied after the
                         decay function, preventing ancient content from
                         crowding out fresh posts regardless of decay shape.
                         Must be >= half_life_hours.
        floor_score:     Minimum score returned by the feature, in [0, 100).
                         A value of 0 means truly stale posts score 0.
                         A value of 5 ensures stale posts still participate
                         in ranking (useful for evergreen content strategies).
    """

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

    # ------------------------------------------------------------------
    # Cross-field validator
    # ------------------------------------------------------------------

    @model_validator(mode="after")
    def max_age_gte_half_life(self) -> "FreshnessConfig":
        """
        Enforce that max_age_hours >= half_life_hours.

        If max_age < half_life, the post would be gated as stale before
        the decay function has had any meaningful effect — the half_life
        parameter would be silently ignored, which is almost certainly
        a misconfiguration.
        """
        if self.max_age_hours < self.half_life_hours:
            raise ValueError(
                f"FreshnessConfig: max_age_hours ({self.max_age_hours}) must be "
                f">= half_life_hours ({self.half_life_hours}).  "
                f"A max_age smaller than half_life causes the staleness gate to "
                f"fire before the decay curve has had any meaningful effect."
            )
        return self
