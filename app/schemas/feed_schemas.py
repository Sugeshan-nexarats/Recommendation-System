from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class FeedRequest(BaseModel):
   
    user_id: int = Field(..., gt=0, description="Authenticated user's ID")
    session_id: str | None = Field(
        default=None, 
        description="The unique session ID identifying this feed instance."
    )
    limit: int = Field(default=20, ge=1, le=100, description="Page size")
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")




class FeatureResultSchema(BaseModel):


    feature_name: str
    score: float = Field(..., ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)



class RankedPost(BaseModel):


    post_id: int
    likes: int
    comments: int
    shares: int
    saves: int
    watch_time: int
    tags: list[str]
    friends: int
    communities: list[str]

    rank: int = Field(
        ...,
        ge=1,
        description="1-indexed position in the ranked feed.  rank=1 is most relevant.",
    )
    relevance_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description=(
            "Final composite relevance score ∈ [0, 1] produced by the "
            "RankingEngine's active scoring strategy."
        ),
    )
    feature_breakdown: dict[str, float] = Field(
        default_factory=dict,
        description=(
            "Weighted contribution of each feature to the final relevance_score. "
            "Values sum to approximately relevance_score. "
            "Populated by the RankingEngine (Stage 4)."
        ),
    )
    features: list[FeatureResultSchema] = Field(
        default_factory=list,
        description=(
            "Raw per-feature signals ∈ [0, 1] from the Feature Framework (Stage 3). "
            "Used as input to the RankingEngine."
        ),
    )

    model_config = {"from_attributes": True}




class FeedResponse(BaseModel):
   
    user_id: int
    session_id: str | None = None
    page: int
    limit: int
    total_returned: int
    posts: list[RankedPost]



class RecommendationBackendItem(BaseModel):
    

    post_id: int
    rank: int = Field(..., ge=1, description="1-indexed rank position.")
    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Final relevance score ∈ [0, 1] from the RankingEngine.",
    )


class RecommendationBackendResponse(BaseModel):
   
    user_id: int
    session_id: str | None = None
    page: int
    limit: int
    recommendations: list[RecommendationBackendItem]
