from abc import ABC, abstractmethod
from app.features.abstract_feature import FeatureResult
from app.retrievers.user_context import UserContext

class AbstractPeopleFeature(ABC):


    @property
    @abstractmethod
    def name(self) -> str:

        ...

    @abstractmethod
    def compute(
        self,
        viewer: UserContext,
        candidate: UserContext
    ) -> FeatureResult:
      
        ...
