from __future__ import annotations
from dataclasses import dataclass, field
from app.models.user_preference import UserPreference
from app.models.user_relationship import UserRelationship

@dataclass(frozen=True, slots=True)
class UserContext:
    
    
    user_id: int
    profile_visibility: str = "public"

    friend_ids:             list[int] = field(default_factory=list)
    following_ids:          list[int] = field(default_factory=list)
    community_ids:          list[int] = field(default_factory=list)
    community_affinity:     dict[str, float] = field(default_factory=dict)
    mutual_friend_ids:      list[int] = field(default_factory=list)
    interacted_author_ids:  list[int] = field(default_factory=list)

    interest_tags: list[str] = field(default_factory=list)
    liked_tags:      list[str] = field(default_factory=list)
    saved_tags:      list[str] = field(default_factory=list)
    watched_tags:    list[str] = field(default_factory=list)
    interacted_tags: list[str] = field(default_factory=list)

    user_preferences: tuple[UserPreference, ...] = field(default_factory=tuple)
    user_relationships: tuple[UserRelationship, ...] = field(default_factory=tuple)
