from __future__ import annotations
import logging
from dataclasses import dataclass, field
from app.features.abstract_feature import AbstractFeature, FeatureResult
from app.features.feature_registry import FeatureRegistry
from app.models.posts import Post
from app.models.user_preference import UserPreference
from app.retrievers.user_context import UserContext

logger = logging.getLogger(__name__)

class AbstractTagMatcher:
 
    def matches(self, preference_name: str, post_tag_set: frozenset[str]) -> bool:
        """Return True if this preference name matches at least one tag."""
        raise NotImplementedError


class ExactTagMatcher(AbstractTagMatcher):


    def matches(self, preference_name: str, post_tag_set: frozenset[str]) -> bool:
        return preference_name in post_tag_set


@dataclass(frozen=True, slots=True)
class _MatchResult:
    """Aggregated result of matching one user's preferences against one post."""

    weighted_score: float
    max_possible: float
    matched_preferences: list[str]
    total_matches: int


@FeatureRegistry.register
class PreferenceFeature(AbstractFeature):


    def __init__(self, matcher: AbstractTagMatcher | None = None) -> None:
        self._matcher = matcher or ExactTagMatcher()

   
    @property
    def name(self) -> str:
        return "preference_score"

    def compute(self, user: UserContext, post: Post, signal_context=None) -> FeatureResult:
 
        if not user.user_preferences:
            return self._empty_result("no_user_preferences")

        post_tags = self._build_tag_set(post)
        if not post_tags:
            return self._empty_result("no_post_tags")

        match = self._run_matching(user.user_preferences, post_tags)
        score = self._normalise(match)

        logger.debug(
            "PreferenceFeature: post_id=%s score=%.4f "
            "matches=%d/%d weighted=%.4f max=%.4f",
            getattr(post, "post_id", "?"),
            score,
            match.total_matches,
            len(user.user_preferences),
            match.weighted_score,
            match.max_possible,
        )

        return FeatureResult(
            feature_name=self.name,
            score=round(score, 6),
            metadata=self._build_metadata(match, score),
        )

    @staticmethod
    def _build_tag_set(post: Post) -> frozenset[str]:

        raw_tags: list | None = getattr(post, "tags", None)
        if not raw_tags:
            return frozenset()
        return frozenset(str(t).strip().lower() for t in raw_tags if t)

    def _run_matching(
        self,
        preferences: tuple[UserPreference, ...],
        post_tag_set: frozenset[str],
    ) -> _MatchResult:

        weighted_score: float = 0.0
        max_possible: float = 0.0
        matched: list[str] = []

        for pref in preferences:
            max_possible += pref.preference_weight
            if self._matcher.matches(pref.preference_name, post_tag_set):
                weighted_score += pref.preference_weight
                matched.append(pref.preference_name)

        return _MatchResult(
            weighted_score=weighted_score,
            max_possible=max_possible,
            matched_preferences=matched,
            total_matches=len(matched),
        )

    @staticmethod
    def _normalise(match: _MatchResult) -> float:
        """Divide weighted score by the maximum possible; clamp to [0, 1]."""
        if match.max_possible == 0.0:
            return 0.0
        raw = match.weighted_score / match.max_possible
        return min(max(raw, 0.0), 1.0)

    def _empty_result(self, reason: str) -> FeatureResult:
        """Return a zero-score result with an explanatory reason key."""
        return FeatureResult(
            feature_name=self.name,
            score=0.0,
            metadata={
                "reason": reason,
                "matched_preferences": [],
                "total_matches": 0,
                "weighted_score": 0.0,
            },
        )

    @staticmethod
    def _build_metadata(match: _MatchResult, score: float) -> dict:
        return {
            "matched_preferences": match.matched_preferences,
            "total_matches": match.total_matches,
            "weighted_score": round(match.weighted_score, 6),
            "max_possible_score": round(match.max_possible, 6),
            "final_score": round(score, 6),
        }
