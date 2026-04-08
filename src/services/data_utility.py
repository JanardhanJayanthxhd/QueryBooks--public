import os
import tempfile

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.core.log import get_logger
from src.core.utility import hash_bytes

logger = get_logger(__name__)


def get_documents_from_file_content(
    content: bytes,
    filename: str,
    user_id: int,
    text_splitter: RecursiveCharacterTextSplitter,
) -> list[Document]:
    """Parses text from a PDF file's binary content, creates document objects,
    and splits them into smaller, embeddable chunks.

    Args:
        content: The raw binary data (Bytes) of the PDF file.
        filename: The name of the file to be used as the 'source' in the document metadata.
        user_id: currently logged in user's id

    Returns:
        A list of chunked Document objects ready for embedding and storage.
    """
    pdf_hash = hash_bytes(data=content)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf_file:
        temp_pdf_file.write(content)
        temp_pdf_filepath = temp_pdf_file.name

    try:
        loader = PyMuPDFLoader(temp_pdf_filepath)
        documents = loader.load()

        for doc in documents:
            doc.metadata["hash"] = pdf_hash
            doc.metadata["source"] = filename
            doc.metadata["user_id"] = user_id

        chunked_documents = text_splitter.split_documents(documents)
        return chunked_documents
    except Exception as e:
        logger.error(f"Error {e}")
        return
    finally:
        if os.path.exists(temp_pdf_filepath):
            os.remove(temp_pdf_filepath)


def get_base_url(url: str) -> str:
    """Extracts the base portion of a URL by removing any fragment identifiers.

    This function splits the URL at the '#' character and returns only the
    preceding part. This is commonly used to normalize URLs and ensure that
    different sections of the same page are treated as the same source.

    Args:
        url: The full URL string, which may include a fragment (e.g., 'example.com/page#section').

    Returns:
        str: The URL without the fragment identifier.
    """
    return url.split("#")[0]


def add_base_url_hash_user_id_to_metadata(
    base_url: str, hash: str, user_id: int, data: list[Document]
) -> None:
    """Injects source URL and unique hash into the metadata of each document chunk.

    Iterates through a list of LangChain Document objects and modifies their
    metadata dictionaries in-place to include tracking information. This is
    essential for filtering or deleting specific sources later in the vector store.

    Args:
        base_url: The sanitized URL string to be used as the 'source'.
        hash: The generated unique identifier for the specific web source.
        user_id: currently logged in user's id
        data: A list of Document objects (chunks) to be updated.

    Returns:
        None
    """
    for doc in data:
        doc.metadata["source"] = base_url
        doc.metadata["hash"] = hash
        doc.metadata["user_id"] = user_id

    if data:
        logger.info(f"Blog document chunk metadata: {data[0].metadata}")
