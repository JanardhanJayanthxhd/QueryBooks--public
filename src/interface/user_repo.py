from abc import ABC, abstractmethod

from src.schema.user import UserCreate


class AbstractUserRepo(ABC):
    @abstractmethod
    def create_user(self, user: UserCreate):
        pass
