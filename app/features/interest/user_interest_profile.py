from __future__ import annotations
from collections import Counter
from dataclasses import dataclass, field
from app.retrievers.user_context import UserContext
from app.models.interaction_weights import INTERACTION_SOURCE_WEIGHTS



@dataclass(frozen=True)
class UserInterestProfile:
   

    tag_weights: Counter      # tag → cumulative weight (float)
    community_ids: frozenset  # frozenset[str]
    source_counts: dict       # source_name → tag count contributed

    @classmethod
    def from_user_context(cls, user: UserContext) -> UserInterestProfile:
       
        weights: Counter = Counter()

        sources = (
            ("explicit",    user.interest_tags),
            ("saved",       user.saved_tags),
            ("liked",       user.liked_tags),
            ("interacted",  user.interacted_tags),
            ("watched",     user.watched_tags),
        )

        source_counts: dict[str, int] = {}
        for source_name, tags in sources:
            weight = INTERACTION_SOURCE_WEIGHTS[source_name]
            count = 0
            for tag in tags:
                normalised = tag.strip().lower()
                if normalised:
                    weights[normalised] += weight
                    count += 1
            source_counts[source_name] = count

        return cls(
            tag_weights=weights,
            community_ids=frozenset(str(c) for c in user.community_ids),
            source_counts=source_counts,
        )

    def is_empty(self) -> bool:
        """True when the user has zero interest signals — cold-start case."""
        return not self.tag_weights and not self.community_ids

    def top_tags(self, n: int = 20) -> list[str]:
        """Return the top N tags by cumulative weight (highest first)."""
        return [tag for tag, _ in self.tag_weights.most_common(n)]

    def total_weight(self) -> float:
        """Sum of all tag weights — used as a normalisation denominator."""
        return sum(self.tag_weights.values())
