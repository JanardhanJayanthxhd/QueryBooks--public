from typing import Optional

from sqlalchemy.orm import Session
from src.core.constants import AIModels
from src.core.log import get_logger
from src.core.utility import CacheDetails
from src.models.cache import UserLLMCache

logger = get_logger(__name__)


def save_to_cache(
    session: Session,
    details: CacheDetails,
    response: str,
    llm: str = AIModels.GPT_4o_MINI.value,
    idx: int = 0,
):
    """
    Save response to cache.

    Args:
        db: Database session
        user_id: User ID
        question: User's question
        response: LLM response to cache
        llm: LLM model name
        idx: Response index (default 0 for single responses)
    """
    existing = (
        session.db.query(UserLLMCache)
        .filter_by(
            user_id=details.user_id,
            prompt=details.question,
            llm=llm,
            idx=idx,
            response=response,
        )
        .first()
    )

    if existing:
        existing.response = response
        logger.info(f"Updated cache for user id: {details.user_id}")
    else:
        new_cache = UserLLMCache(
            user_id=details.user_id,
            prompt=details.question,
            llm=llm,
            idx=idx,
            response=response,
        )
        session.db.add(new_cache)
        logger.info(f"Cached new response for user id: {details.user_id}")

    session.db.commit()


def get_cached_response(
    session: Session, details: CacheDetails, llm: str = AIModels.GPT_4o_MINI.value
) -> Optional[str]:
    cached = (
        session.db.query(UserLLMCache)
        .filter_by(user_id=details.user_id, prompt=details.question, llm=llm)
        .first()
    )

    if cached:
        logger.info(f"Cache HIT for user: {details.user_id}")
        return cached.response

    logger.info(f"Cache HIT for user: {details.user_id}")
    return None
