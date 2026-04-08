from typing import Optional

from sqlalchemy.orm import Session
from src.core.log import get_logger
from src.core.utility import CacheDetails
from src.interface.cache_repo import AbstractCacheRepo
from src.models.cache import UserLLMCache

logger = get_logger(__name__)


class CacheRepository(AbstractCacheRepo):
    def __init__(self, session: Session) -> None:
        self.session = session

    def fetch_cache_by_prompt_and_response(
        self, details: CacheDetails, response: str, llm: str, idx: int = 0
    ) -> Optional[UserLLMCache]:
        return (
            self.session.query(UserLLMCache)
            .filter_by(
                user_id=details.user_id,
                prompt=details.question,
                llm=llm,
                idx=idx,
                response=response,
            )
            .first()
        )

    def fetch_cache_by_prompt(self, details: CacheDetails, llm: str):
        return (
            self.session.query(UserLLMCache)
            .filter_by(user_id=details.user_id, prompt=details.question, llm=llm)
            .first()
        )

    def update_cache(self, existing_cache: UserLLMCache, new_response: str) -> None:
        existing_cache.response = new_response
        self.session.commit()
        logger.info("Updated cache")

    def add_cache(
        self, details: CacheDetails, llm: str, idx: int, response: str
    ) -> None:
        pass
        new_cache = UserLLMCache(
            user_id=details.user_id,
            prompt=details.question,
            llm=llm,
            idx=idx,
            response=response,
        )
        self.session.add(new_cache)
        self.session.commit()
        logger.info(f"Cached new response for user id: {details.user_id}")
