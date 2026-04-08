from typing import Optional

from src.core.constants import settings
from src.core.log import get_logger
from src.core.utility import CacheDetails
from src.interface.cache_repo import AbstractCacheRepo
from src.interface.cache_service import AbstractCacheService

logger = get_logger(__name__)


class CacheService(AbstractCacheService):
    def __init__(self, repo: AbstractCacheRepo) -> None:
        self.repo = repo

    def save_to_cache(
        self,
        details: CacheDetails,
        response: str,
        idx: int = 0,
    ) -> None:
        existing_cache = self.repo.fetch_cache_by_prompt_and_response(
            details=details, response=response, llm=settings.LLM_NAME, idx=idx
        )
        if existing_cache:
            self.repo.update_cache(existing_cahce=existing_cache)
        else:
            self.repo.add_cache(
                details=details, llm=settings.LLM_NAME, idx=idx, response=response
            )

    def get_cached_response(
        self,
        details: CacheDetails,
    ) -> Optional[str]:
        cached = self.repo.fetch_cache_by_prompt(details=details, llm=settings.LLM_NAME)
        if cached:
            logger.info(f"Cache HIT for user: {details.user_id}")
            return cached.response

        logger.info(f"Cache HIT for user: {details.user_id}")
        return None
