import uuid
import logging
from app.sessions.abstract_session_provider import AbstractSessionProvider

logger = logging.getLogger(__name__)

class DevSessionProvider(AbstractSessionProvider):

    
    def __init__(self) -> None:
        # Maps user_id to their active development session_id
        self._user_sessions: dict[int, str] = {}
        
    def get_session_id(
        self, 
        user_id: int, 
        provided_session_id: str | None = None, 
        is_new_session: bool = False
    ) -> tuple[str, bool]:
       
        
        if provided_session_id:
            logger.debug(
                "DevSessionProvider: using client-provided session_id '%s' for user_id=%d",
                provided_session_id, user_id
            )
          
            self._user_sessions[user_id] = provided_session_id
            return provided_session_id, is_new_session
            
        
        if is_new_session or user_id not in self._user_sessions:
            new_session_id = f"dev-session-{uuid.uuid4()}"
            self._user_sessions[user_id] = new_session_id
            logger.info(
                "DevSessionProvider: generated new session_id '%s' for user_id=%d",
                new_session_id, user_id
            )
            return new_session_id, True
            
       
        existing_session_id = self._user_sessions[user_id]
        logger.debug(
            "DevSessionProvider: reusing existing session_id '%s' for user_id=%d",
            existing_session_id, user_id
        )
        return existing_session_id, False
