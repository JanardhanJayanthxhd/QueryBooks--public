from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from src.models.base import Base


class UserLLMCache(Base):
    """Stores cached responses from Large Language Models (LLMs) per user.

    This model implements a composite primary key to ensure that the same prompt
    processed by the same LLM for the same user results in a unique cache entry.
    It is used to reduce API latency and costs by serving pre-generated responses
    for identical queries.

    Attributes:
        idx (int): An incremental index part of the composite primary key.
        user_id (int): Foreign key referencing the 'user' table; entries are
            deleted if the user is removed (CASCADE).
        llm (str): The name or identifier of the LLM used (e.g., 'gpt-4o-mini').
        prompt (str): The raw input text sent to the LLM.
        response (str): The generated output text received from the LLM.

    Table Args:
        idx_user_prompt: A composite index on user_id and prompt to speed up
        cache lookups for specific user queries.
    """

    __tablename__ = "user_llm_cache"

    idx: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    llm: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    prompt: Mapped[str] = mapped_column(Text, primary_key=True, nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (Index("idx_user_prompt", "user_id", "prompt"),)
