from langchain_ollama.embeddings import OllamaEmbeddings
from langchain_openai import OpenAIEmbeddings
from src.core.constants import settings


def get_embedding():
    if settings.LLM_PROVIDER == "openai":
        return OpenAIEmbeddings(
            model=settings.OPENAI_EMBEDDING_MODEL, api_key=settings.OPENAI_API_KEY
        )
    elif settings.LLM_PROVIDER == "ollama":
        return OllamaEmbeddings(
            model=settings.OLLAMA_EMBEDDING_MODEL,
            base_url=settings.OLLAMA_BASE_URL
        )
    else:
        raise Exception("Unknown llm provider")
