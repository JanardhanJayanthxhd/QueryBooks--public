from src.core.constants import settings
from src.core.log import logger
from src.services.base_ai_service import BaseAIService
from src.services.ai_utility import (
    calculate_token_cost,
)


class OpenAIService(BaseAIService):
    def __init__(self) -> None:
        super().__init__()

    def _get_token_cost(self, usage_metadata: dict | None):
        try:
            token_cost = calculate_token_cost(
                usage_metadata, model_name=settings.OPENAI_MODEL
            )
        except Exception as e:
            logger.info(f"Error occured while calculating token cost: {e}")
            token_cost = "Unable to calculate token cost"
        return token_cost
