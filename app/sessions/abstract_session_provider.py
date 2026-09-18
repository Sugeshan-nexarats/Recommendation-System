from abc import ABC, abstractmethod

class AbstractSessionProvider(ABC):

    @abstractmethod
    def get_session_id(
        self, 
        user_id: int, 
        provided_session_id: str | None = None, 
        is_new_session: bool = False
    ) -> tuple[str, bool]:
       
        pass
