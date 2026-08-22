from __future__ import annotations
from dataclasses import dataclass

RELATIONSHIP_TYPE_FRIEND: str = "FRIEND"
RELATIONSHIP_TYPE_FOLLOW: str  = "FOLLOW"
RELATIONSHIP_TYPE_BLOCK: str   = "BLOCK"
STATUS_ACCEPTED: str = "ACCEPTED"
STATUS_PENDING:  str = "PENDING"
STATUS_REJECTED: str = "REJECTED"
STATUS_BLOCKED:  str = "BLOCKED"
STATUS_REMOVED:  str = "REMOVED"

ACTIVE_STATUSES: frozenset[str] = frozenset({STATUS_ACCEPTED})

@dataclass(frozen=True, slots=True)
class UserRelationship:

    requester_user_id: int
    target_user_id:    int
    relationship_type: str
    status:            str

    @property
    def is_accepted(self) -> bool:
       
        return self.status == STATUS_ACCEPTED

    @property
    def is_accepted_friend(self) -> bool:
        
        return self.relationship_type == RELATIONSHIP_TYPE_FRIEND and self.is_accepted

    @property
    def is_block(self) -> bool:
        
        return self.relationship_type == RELATIONSHIP_TYPE_BLOCK
