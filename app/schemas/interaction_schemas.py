from pydantic import BaseModel, Field, validator
from typing import Optional

class InteractionRequest(BaseModel):
    user_id: int
    post_id: int
    interaction_type: str = Field(..., description="Must be one of: like, save, watch, comment, share")
    watch_time: Optional[int] = None
    
    @validator("interaction_type")
    def validate_type(cls, v):
        allowed = {"like", "save", "watch", "comment", "share"}
        if v not in allowed:
            raise ValueError(f"Invalid interaction_type. Allowed: {allowed}")
        return v

class InteractionResponse(BaseModel):
    status: str = "success"
    message: str
