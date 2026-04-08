from abc import ABC, abstractmethod


class AbstractDataRepo(ABC):
    @abstractmethod
    def add_documents(self, documents: list) -> None:
        pass
