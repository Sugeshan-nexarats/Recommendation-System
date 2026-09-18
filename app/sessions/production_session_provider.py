import logging
from fastapi import HTTPException
from app.sessions.abstract_session_provider import AbstractSessionProvider

logger = logging.getLogger(__name__)

class ProductionSessionProvider(AbstractSessionProvider):

    
    def get_session_id(
        self, 
        user_id: int, 
        provided_session_id: str | None = None, 
        is_new_session: bool = False
    ) -> tuple[str, bool]:
        if not provided_session_id:
            logger.error("ProductionSessionProvider: missing session_id for user_id=%d", user_id)
            raise HTTPException(
                status_code=400, 
                detail="session_id is required in production."
            )
            
        logger.debug(
            "ProductionSessionProvider: using Java-provided session_id '%s' for user_id=%d (is_new_session=%s)",
            provided_session_id, user_id, is_new_session
        )
        return provided_session_id, is_new_session
