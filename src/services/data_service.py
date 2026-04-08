from langchain_community.document_loaders import WebBaseLoader
from src.core.utility import hash_bytes, hash_str
from src.interface.data_repo import AbstractDataRepo
from src.interface.data_service import AbstractDataService
from src.services.data_utility import (
    add_base_url_hash_user_id_to_metadata,
    get_base_url,
    get_documents_from_file_content,
)


class DataService(AbstractDataService):
    def __init__(self, repo: AbstractDataRepo) -> None:
        self.repo = repo

    def add_web_content_as_embedding(self, url: str, user_id: int) -> str:
        """Fetches web content, processes it, and embeds it with metadata into the vector store.

        This function performs a check to prevent duplicate entries based on the URL.
        If unique, it loads the webpage content, generates a hash of the base URL,
        splits the text into chunks, injects source and hash metadata into each chunk,
        and saves them to the PGVector store.

        Args:
            url: The full URL of the web page to be processed.
            user_id: id for currently logged in user from db

        Returns:
            A status message indicating if the URL was already present or successfully added.
        """
        if self.repo.check_existing_hash(hash=hash_str(data=get_base_url(url=url))):
            return f"web - {url} - already exists"

        docs = WebBaseLoader([url]).load()
        base_url = get_base_url(url=url)
        web_url_hash = hash_str(data=base_url)
        web_document_chunks = self.repo.text_splitter.split_documents(docs)

        add_base_url_hash_user_id_to_metadata(
            base_url=base_url,
            hash=web_url_hash,
            user_id=user_id,
            data=web_document_chunks,
        )

        self.repo.add_documents(web_document_chunks)
        return f"web - {url} - added successfully"

    def add_pdf_as_embedding(self, content: bytes, filename: str, user_id: int) -> str:
        """Checks if a file already exists in the vector store and, if not, processes
        the file contents, chunks the text, creates embeddings, and adds them to the database.

              Args:
                  contents: The raw binary data (Bytes) of the PDF file.
                  filename: The name of the file, used as the unique identifier and source metadata.
                  current_user_id: id for currently logged in user from db

              Returns:
                  A string message indicating whether the file was successfully added or
                  if it already existed.
        """
        if self.repo.check_existing_hash(hash=hash_bytes(data=content)):
            return f"File - {filename} - already exists"
        documents = get_documents_from_file_content(
            content=content,
            filename=filename,
            user_id=user_id,
            text_splitter=self.repo.text_splitter,
        )
        self.repo.vector_store.add_documents(documents)
        return f"File - {filename} - added successfully"
