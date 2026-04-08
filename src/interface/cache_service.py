from abc import ABC, abstractmethod
from typing import Optional

from src.core.utility import CacheDetails


class AbstractCacheService(ABC):
    @abstractmethod
    def save_to_cache(
        self,
        details: CacheDetails,
        response: str,
        llm: str,
        idx: int,
    ) -> None:
        pass

    @abstractmethod
    def get_cached_response(self, details: CacheDetails, llm: str) -> Optional[str]:
        pass
