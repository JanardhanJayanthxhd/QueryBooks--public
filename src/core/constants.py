from enum import Enum
from pathlib import Path
from typing import Literal, Self

from dotenv import load_dotenv
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings
from src.design_patterns.singleton import Singleton

load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / ".env")


# General
class ResponseType(Enum):
    SUCCESS = "success"
    ERROR = "error"


class Settings(BaseSettings, metaclass=Singleton):
    LLM_NAME: str | None = None

    # required
    POSTGRESQL_DB_NAME: str = Field(alias="POSTGRESQL_DB_NAME")
    POSTGRESQL_PORT: str = Field(alias="POSTGRESQL_PORT")
    POSTGRESQL_PWD: str = Field(alias="POSTGRESQL_PWD")
    POSTGRESQL_HOST: str = Field(alias="POSTGRESQL_HOST")
    JWT_SECRET_KEY: str = Field(default="the-secret-key", alias="JWT_SECRET_KEY")

    LLM_PROVIDER: Literal["openai", "ollama"] = Field(
        default="openai", alias="LLM_PROVIDER"
    )

    # openi
    OPENAI_API_KEY: str | None = Field(alias="OPENAI_API_KEY")
    OPENAI_MODEL: str | None = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    OPENAI_EMBEDDING_MODEL: str | None = Field(
        default="text-embedding-large-3", alias="OPENAI_EMBEDDING_MODEL"
    )

    # ollama
    OLLAMA_MODEL: str | None = Field(default="mistral:7b", alias="OLLAMA_MODEL")
    OLLAMA_EMBEDDING_MODEL: str | None = Field(
        default="nomic-embed-text:latest", alias="OLLAMA_EMBEDDING_MODEL"
    )
    OLLAMA_BASE_URL: str | None = Field(
        default='http://localhost:11434', alias="OLLAMA_BASE_URL"
    )

    @model_validator(mode="after")
    def check_required_attributes(self) -> Self:
        if self.LLM_PROVIDER == "openai":
            missing = [
                k
                for k in ["OPENAI_API_KEY", "OPENAI_MODEL", "OPENAI_EMBEDDING_MODEL"]
                if not getattr(self, k)
            ]
            self.LLM_NAME = self.OLLAMA_MODEL
        elif self.LLM_PROVIDER == "ollama":
            missing = [
                k
                for k in ["OLLAMA_MODEL", "OLLAMA_EMBEDDING_MODEL"]
                if not getattr(self, k)
            ]
            self.LLM_NAME = self.OLLAMA_MODEL
        else:
            # TODO: make a custom exception in future
            raise Exception("Unsupported llm provider")

        if missing:
            raise ValueError("Attribute missing error ")

        return self

    class Config:
        env_file = "../../.env"
        env_file_encoding = "utf-8"


settings = Settings()

# Defaults
CONNECTION: str = (
    f"postgresql+psycopg://postgres:{settings.POSTGRESQL_PWD}@{settings.POSTGRESQL_HOST}:{settings.POSTGRESQL_PORT}/{settings.POSTGRESQL_DB_NAME}"
)
MODEL_COST_PER_MILLION_TOKENS: dict[str, dict[str, float]] = {
    "gpt-4o-mini": {"i": 0.15, "o": 0.60},
}
HISTORY: list = []
