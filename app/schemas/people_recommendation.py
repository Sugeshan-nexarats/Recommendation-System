from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class PeopleRequest(BaseModel):

    user_id: int = Field(..., gt=0, description="Authenticated user's ID")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum number of users to return")
    cursor: Optional[int] = Field(default=None, description="Pagination cursor (e.g., offset or last seen user id)")


class PeopleRecommendationItem(BaseModel):
   
    recommended_user_id: int
    rank: int = Field(..., ge=1, description="1-indexed rank position. rank=1 is best.")
    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Final composite relevance score ∈ [0, 1] produced by the PeopleEngine."
    )
    reasons: list[str] = Field(
        default_factory=list,
        description="Deterministic explanations for why this user was recommended."
    )


class PeopleResponse(BaseModel):
   
    user_id: int
    total_returned: int
    recommendations: list[PeopleRecommendationItem]
    next_cursor: Optional[int] = Field(default=None, description="Cursor for the next page of results")
