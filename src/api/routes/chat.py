import time

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.core.constants import ResponseType
from src.core.database import get_db
from src.core.jwt_utility import authenticate_user_from_token
from src.core.log import get_logger
from src.core.utility import (
    CacheDetails,
    clean_llm_output,
    get_elapsed_time_till_now_in_ms,
)
from src.factory.ai_service_factory import get_ai_service
from src.interface.ai_service import AbstractAIService
from src.interface.cache_service import AbstractCacheService
from src.models.user import User
from src.repository.cache_repo import CacheRepository
from src.schema.ai import Query
from src.schema.response import APIResponse
from src.services.cache_service import CacheService

chat = APIRouter()
logger = get_logger(__name__)


def get_cache_service(session: Session = Depends(get_db)) -> AbstractCacheService:
    return CacheService(repo=CacheRepository(session=session))


@chat.post("/chat", response_model=APIResponse)
async def search_from_db(
    query: Query,
    current_user: User = Depends(authenticate_user_from_token),
    cache_service: AbstractCacheService = Depends(get_cache_service),
    ai_service: AbstractAIService = Depends(get_ai_service),
):
    """
    Performs a query using a Conversational RAG chain against the vector database.

    The query is answered based on the documents stored in the database,
    maintaining conversational history. The chat history is updated after
    the response is generated. Calculates and returns the token cost.

    Args:
        query: The user's query wrapped in a Query schema object.

    Returns:
        A dictionary with the response status and a message containing the
        cleaned AI's response and the calculated token cost.

    Raises:
        HTTPException: If an error occurs during the RAG chain invocation,
                       a 400 Bad Request is raised.
    """
    start_time: float = time.perf_counter()
    logger.info(f"CURRENT USER EMAIL: {current_user.email}")
    try:
        cached_response = cache_service.get_cached_response(
            details=CacheDetails(
                user_id=current_user.id,
                question=query.query,
            )
        )

        if cached_response:
            return APIResponse(
                response=ResponseType.SUCCESS,
                message={
                    "response time": f"{get_elapsed_time_till_now_in_ms(start_time=start_time):.0f}ms",
                    "query response": clean_llm_output(cached_response),
                },
            )

        logger.info("Invoking RAG chain")

        result, token_cost = ai_service.chat(query=query.query, user_id=current_user.id)

        cache_service.save_to_cache(
            details=CacheDetails(
                user_id=current_user.id,
                question=query.query,
            ),
            response=result,
        )

        return APIResponse(
            response=ResponseType.SUCCESS,
            message={
                "response time": f"{get_elapsed_time_till_now_in_ms(start_time=start_time):.0f}ms",
                "token cost": token_cost,
                "query response": result,
            },
        )
    except Exception as e:
        logger.error(f"Error {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error while chatting with AI, please try again.",
        )
