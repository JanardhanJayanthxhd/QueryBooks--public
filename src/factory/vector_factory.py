from langchain_postgres import PGVector
from src.core.constants import CONNECTION, settings
from src.factory.embedding_factory import get_embedding


def get_vector_store(connection: str = CONNECTION):
    # uses CONNECTION from constants.py by default
    if settings.LLM_PROVIDER == "openai":
        return PGVector(
            embeddings=get_embedding(),
            collection_name="uploaded_documents",
            connection=connection,
            use_jsonb=True,
        )
    elif settings.LLM_PROVIDER == "ollama":
        return PGVector(
            embeddings=get_embedding(),
            collection_name="local_uploaded_docs",
            connection=connection,
            use_jsonb=True,
        )
    else:
        raise Exception("Unknown llm provider")
