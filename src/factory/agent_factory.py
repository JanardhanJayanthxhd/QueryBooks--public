from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from src.core.constants import settings


def get_agent():
    if settings.LLM_PROVIDER == "openai":
        return ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0,
            api_key=settings.OPENAI_API_KEY,
            stream_usage=True,
        )
    elif settings.LLM_PROVIDER == "ollama":
        return ChatOllama(
            model=settings.OLLAMA_MODEL, 
            temperature=0,
            base_url=settings.OLLAMA_BASE_URL
        )
    else:
        raise Exception("Unknown llm provider")
