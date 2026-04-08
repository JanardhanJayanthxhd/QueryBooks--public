import psycopg
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.core.constants import settings
from src.core.log import get_logger
from src.factory.vector_factory import get_vector_store
from src.interface.data_repo import AbstractDataRepo

logger = get_logger(__name__)


class DataRepository(AbstractDataRepo):
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200) -> None:
        self.chunk_size: int = chunk_size
        self.chunk_overlap: int = chunk_overlap
        self.__connection: str = (
            f"postgresql+psycopg://postgres:{settings.POSTGRESQL_PWD}@{settings.POSTGRESQL_HOST}:{settings.POSTGRESQL_PORT}/{settings.POSTGRESQL_DB_NAME}"
        )

    def __get_filter_metadata_by_hash_sql_query(self) -> str:
        return """
            SELECT id, document, cmetadata
            FROM langchain_pg_embedding
            WHERE cmetadata->>'hash' = %s
        """

    @property
    def vector_store(self):
        """Returns an instance of the Vector Store"""
        return get_vector_store(self.__connection)

    @property
    def text_splitter(self):
        return RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""],
        )

    def check_existing_hash(self, hash: str) -> bool:
        pg_connection = self.__connection.replace(
            "postgresql+psycopg://", "postgresql://"
        )
        try:
            with psycopg.connect(pg_connection) as conn:
                with conn.cursor() as cur:
                    cur.execute(self.__get_filter_metadata_by_hash_sql_query(), (hash,))
                    results = cur.fetchall()
                    exists = len(results) > 0
                    return exists
        except Exception as e:
            logger.error(f"Error: {e}")
            return False

    def add_documents(self, documents: list[Document]):
        self.vector_store.add_documents(documents)
