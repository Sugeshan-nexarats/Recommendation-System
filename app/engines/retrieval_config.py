from __future__ import annotations
from pydantic import BaseModel, Field

class RetrievalConfig(BaseModel):

    preference_limit: int = Field(default=40, ge=1, description="PreferenceRetriever budget")
    trending_limit:   int = Field(default=20, ge=1, description="TrendingRetriever budget")
    recent_limit:     int = Field(default=20, ge=1, description="RecentRetriever budget")
    default_limit:    int = Field(default=10, ge=1, description="Fallback for unknown retrievers")

    model_config = {"frozen": True}

    def limit_for(self, retriever_name: str) -> int:

        _limit_map: dict[str, int] = {
            "preference_retriever": self.preference_limit,
            "trending_retriever":   self.trending_limit,
            "recent_retriever":     self.recent_limit,
        }
        return _limit_map.get(retriever_name, self.default_limit)
