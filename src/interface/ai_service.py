from abc import ABC, abstractmethod


class AbstractAIService(ABC):
    @abstractmethod
    def interact(self, user_message: str) -> tuple:
        pass

    @abstractmethod
    def chat(self, query: str, user_id: int) -> None:
        pass
