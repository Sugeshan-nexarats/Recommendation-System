

from abc import ABC, abstractmethod
from typing import Optional

from app.ranking.ranking_result import RankingResult


class AbstractFeedSessionRepository(ABC):

    @abstractmethod
    def save_pool(
        self,
        session_id: str,
        user_id: int,
        ranked_results: list[RankingResult],
    ) -> None:

        ...

    @abstractmethod
    def get_session_page_and_meta(
        self,
        session_id: str,
        page: int,
        limit: int,
    ) -> tuple[dict[str, str], list[int]] | None:

        ...

    @abstractmethod
    def update_scores(self, session_id: str, ranked_results: list[RankingResult]) -> None:

        ...

    @abstractmethod
    def delete_session(self, session_id: str) -> None:
 
        ...

