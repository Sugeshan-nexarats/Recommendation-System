"""
AbstractDecayFunction — Strategy interface for freshness decay curves.

The decay function maps post age (in hours) to a freshness score in [0, 1].
It is the core mathematical component of FreshnessFeature and is the primary
extension point for tuning the shape of the freshness signal.

Available implementations:
    ExponentialDecayFunction — default; smooth, aggressive early decay.
    LinearDecayFunction      — simple, fully explainable.
    StepDecayFunction        — binary freshness window (on/off at half_life).

Adding a new decay shape:
    1. Create my_decay.py implementing AbstractDecayFunction.
    2. Inject via FreshnessFeature(decay_function=MyDecay(...)).
    No other code changes needed.

Contract:
    apply(age_hours, config) → [0.0, 1.0]
    - age_hours=0 MUST return 1.0 (brand-new post is maximally fresh).
    - age_hours >= config.max_age_hours SHOULD return config.floor_score / 100.
    - The function MUST be monotonically non-increasing.
    - MUST NOT raise; return floor_score / 100 on any error.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.features.freshness.freshness_config import FreshnessConfig


class AbstractDecayFunction(ABC):
    """
    Strategy interface for freshness decay curves.

    All implementations MUST:
      - Be stateless and safe for concurrent use.
      - Accept age_hours ≥ 0.
      - Return values in [0.0, 1.0].
      - Never raise exceptions.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Canonical name of this decay function (snake_case)."""
        ...

    @abstractmethod
    def apply(self, age_hours: float, config: FreshnessConfig) -> float:
        """
        Map post age to a freshness multiplier in [0.0, 1.0].

        Args:
            age_hours: Post age in fractional hours (>= 0).
            config:    Active FreshnessConfig providing half_life_hours,
                       max_age_hours, and floor_score.

        Returns:
            Freshness multiplier in [0.0, 1.0].
            Multiply by 100 to get the 0-100 freshness score.
        """
        ...
