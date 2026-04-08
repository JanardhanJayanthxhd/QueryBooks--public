from src.services.base_ai_service import BaseAIService


class LocalAIService(BaseAIService):
    def __init__(self):
        super().__init__()
        self.__token_response: str = "cannot calculate token cost for local llm"

    def _get_token_cost(self, usage_metadata: dict | None):
        return self.__token_response
