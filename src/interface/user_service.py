from abc import ABC, abstractmethod

from src.models.user import User
from src.schema.user import UserCreate, UserLogin


class AbstractUserService(ABC):
    @abstractmethod
    def login_user(self, user: UserLogin) -> None:
        pass

    @abstractmethod
    def register_user(self, user: UserCreate) -> User:
        pass
