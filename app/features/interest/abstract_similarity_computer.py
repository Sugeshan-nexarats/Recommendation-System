from __future__ import annotations
from abc import ABC, abstractmethod
from app.features.interest.user_interest_profile import UserInterestProfile


class AbstractSimilarityComputer(ABC):

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def tag_similarity(
        self,
        profile: UserInterestProfile,
        post_tags: frozenset[str],
    ) -> float:
        """
        Compute similarity between the user's interest profile and a post's tags.
        """
        ...

    @abstractmethod
    def community_similarity(
        self,
        profile: UserInterestProfile,
        post_communities: frozenset[str],
    ) -> float:
        """
        Compute overlap between the user's communities and the post's communities.
        """
        ...
