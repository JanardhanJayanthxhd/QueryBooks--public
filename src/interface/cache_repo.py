from abc import ABC, abstractmethod

from src.core.utility import CacheDetails
from src.models.cache import UserLLMCache


class AbstractCacheRepo(ABC):
    @abstractmethod
    def fetch_cache_by_prompt_and_response(
        self, details: CacheDetails, response: str, llm: str, idx: int
    ):
        pass

    @abstractmethod
    def fetch_cache_by_prompt(self, details: CacheDetails, llm: str):
        pass

    @abstractmethod
    def update_cache(self, existing_cache: UserLLMCache, new_response: str) -> None:
        pass

    @abstractmethod
    def add_cache(
        self, details: CacheDetails, llm: str, idx: int, response: str
    ) -> None:
        pass
