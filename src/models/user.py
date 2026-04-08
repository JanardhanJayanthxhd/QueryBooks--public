from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from src.models.base import Base


class User(Base):
    """Represents a user entity in the system.

    This model stores essential user account information, including unique
    identifiers for authentication and contact. It serves as the primary
    identity provider for other application features like LLM caching.

    Attributes:
        id (int): Unique identifier and primary key for the user.
        name (str): The user's full name or username; must be unique.
        email (str): The user's email address; used for login and must be unique.
        password_hash (str): The securely hashed version of the user's password.
    """

    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
