from abc import ABC, abstractmethod


class AbstractDataService(ABC):
    @abstractmethod
    def add_web_content_as_embedding(self, url: str, user_id: int) -> str:
        pass

    @abstractmethod
    def add_pdf_as_embedding(self, content: bytes, filename: str, user_id: int) -> str:
        pass
