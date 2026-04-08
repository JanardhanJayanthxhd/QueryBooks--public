from src.core.constants import settings
from src.interface.ai_service import AbstractAIService
from src.services.local_ai_service import LocalAIService
from src.services.openai_service import OpenAIService


def get_ai_service() -> AbstractAIService:
    if settings.LLM_PROVIDER == "openai":
        return OpenAIService()
    elif settings.LLM_PROVIDER == "ollama":
        return LocalAIService()
    else:
        raise Exception("Unknown llm provider")
