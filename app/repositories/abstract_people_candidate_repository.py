import abc
from typing import List

class AbstractPeopleCandidateRepository(abc.ABC):
   

    @abc.abstractmethod
    def get_candidates_by_shared_interests(self, user_id: int, limit: int = 100) -> List[int]:
      
        pass

    @abc.abstractmethod
    def get_candidates_by_mutual_connections(self, user_id: int, limit: int = 100) -> List[int]:
     
        pass
