from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from langchain_core.documents import Document
from src.core.utility import hash_password


class TestUserAuthentication:
    """Tests for user authentication functions"""

    def test_authenticate_user_success(self, test_db_session):
        """Test successful user authentication"""
        from src.models.user import User
        from src.repository.user_repo import UserRepository
        from src.schema.user import UserLogin

        # Create user
        user = User(
            name="Auth User",
            email="auth@test.com",
            password_hash=hash_password("correctpass"),
        )
        test_db_session.add(user)
        test_db_session.commit()

        # Authenticate
        repo = UserRepository(session=test_db_session)
        login = UserLogin(email="auth@test.com", password="correctpass")
        result = repo.authenticate_user(user=login)

        assert result is not None
        assert result.email == "auth@test.com"

    def test_authenticate_user_wrong_password(self, test_db_session):
        """Test authentication with wrong password"""
        from src.models.user import User
        from src.repository.user_repo import UserRepository
        from src.schema.user import UserLogin

        user = User(
            name="Auth User",
            email="auth@test.com",
            password_hash=hash_password("correctpass"),
        )
        test_db_session.add(user)
        test_db_session.commit()

        repo = UserRepository(session=test_db_session)
        login = UserLogin(email="auth@test.com", password="wrongpass")

        with pytest.raises(HTTPException) as exc_info:
            repo.authenticate_user(user=login)

        assert exc_info.value.status_code == 401
        assert "Invalid email or password" in exc_info.value.detail

    def test_authenticate_user_not_found(self, test_db_session):
        """Test authentication with non-existent user"""
        from src.repository.user_repo import UserRepository
        from src.schema.user import UserLogin

        repo = UserRepository(session=test_db_session)
        login = UserLogin(email="notfound@test.com", password="pass")

        with pytest.raises(HTTPException) as exc_info:
            repo.authenticate_user(user=login)

        assert exc_info.value.status_code == 401
        assert "Unable to find user" in exc_info.value.detail


class TestUserManagement:
    """Tests for user management functions"""

    def test_fetch_user_by_email_found(self, test_db_session, test_user):
        """Test fetching existing user by email"""
        from src.repository.user_repo import UserRepository

        repo = UserRepository(session=test_db_session)
        user = repo.fetch_existing_user_by_email(email=test_user.email)

        assert user is not None
        assert user.email == test_user.email
        assert user.id == test_user.id

    def test_fetch_user_by_email_not_found(self, test_db_session):
        """Test fetching non-existent user returns None"""
        from src.repository.user_repo import UserRepository

        repo = UserRepository(session=test_db_session)
        user = repo.fetch_existing_user_by_email(email="nonexistent@test.com")

        assert user is None

    def test_check_existing_user_exists(self, test_db_session, test_user):
        """Test checking if user exists returns a user object"""
        from src.repository.user_repo import UserRepository

        repo = UserRepository(session=test_db_session)
        existing = repo.fetch_existing_user_by_email(email=test_user.email)

        assert existing is not None

    def test_check_existing_user_not_exists(self, test_db_session):
        """Test checking non-existent user returns None"""
        from src.repository.user_repo import UserRepository

        repo = UserRepository(session=test_db_session)
        existing = repo.fetch_existing_user_by_email(email="new@test.com")

        assert existing is None

    def test_add_commit_refresh_db(self, test_db_session):
        """Test database add/commit/refresh helper"""
        from src.models.user import User
        from src.repository.utility import add_commit_refresh_db

        new_user = User(
            name="New User",
            email="newuser@test.com",
            password_hash=hash_password("pass123"),
        )

        add_commit_refresh_db(object=new_user, db=test_db_session)

        # User should have ID after commit
        assert new_user.id is not None

        # Should be retrievable from DB
        retrieved = (
            test_db_session.query(User).filter_by(email="newuser@test.com").first()
        )
        assert retrieved is not None


class TestFileUpload:
    """Tests for file upload and processing functions"""

    @patch("src.repository.data_repo.DataRepository.check_existing_hash")
    @patch("src.services.data_service.get_documents_from_file_content")
    @patch("src.repository.data_repo.get_vector_store")
    def test_add_file_as_embedding_success(
        self, mock_vector_store, mock_get_docs, mock_check_hash
    ):
        """Test successful file embedding addition"""
        from src.repository.data_repo import DataRepository
        from src.services.data_service import DataService

        mock_check_hash.return_value = False
        mock_docs = [Document(page_content="Test", metadata={})]
        mock_get_docs.return_value = mock_docs

        mock_store = MagicMock()
        mock_vector_store.return_value = mock_store

        repo = DataRepository()
        service = DataService(repo=repo)
        result = service.add_pdf_as_embedding(
            content=b"PDF content", filename="test.pdf", user_id=1
        )

        assert result.endswith("added successfully")

    @patch("src.repository.data_repo.DataRepository.check_existing_hash")
    def test_add_file_as_embedding_duplicate(self, mock_check_hash):
        """Test adding duplicate file"""
        from src.repository.data_repo import DataRepository
        from src.services.data_service import DataService

        mock_check_hash.return_value = True

        repo = DataRepository()
        service = DataService(repo=repo)
        result = service.add_pdf_as_embedding(
            content=b"PDF content", filename="duplicate.pdf", user_id=1
        )

        assert "already exists" in result

    @patch("src.services.data_utility.PyMuPDFLoader")
    def test_get_documents_from_file_content(self, mock_loader):
        """Test extracting documents from PDF content"""
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        from src.services.data_utility import get_documents_from_file_content

        mock_loader_instance = MagicMock()
        mock_doc = Document(page_content="PDF text", metadata={})
        mock_loader_instance.load.return_value = [mock_doc]
        mock_loader.return_value = mock_loader_instance

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200
        )
        contents = b"%PDF-1.4 content"
        result = get_documents_from_file_content(
            contents, "test.pdf", user_id=1, text_splitter=text_splitter
        )

        assert result is not None
        assert len(result) > 0

    @patch("src.services.data_utility.PyMuPDFLoader")
    def test_get_documents_from_file_content_error(self, mock_loader):
        """Test error handling in document extraction"""
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        from src.services.data_utility import get_documents_from_file_content

        mock_loader.side_effect = Exception("PDF parsing error")

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200
        )
        contents = b"Invalid PDF"
        result = get_documents_from_file_content(
            contents, "bad.pdf", user_id=1, text_splitter=text_splitter
        )

        assert result is None


class TestWebContentUpload:
    """Tests for web content upload functions"""

    @patch("src.repository.data_repo.DataRepository.check_existing_hash")
    @patch("src.services.data_service.WebBaseLoader")
    @patch("src.repository.data_repo.get_vector_store")
    def test_add_web_content_success(
        self, mock_vector_store, mock_web_loader, mock_check_hash
    ):
        """Test successful web content addition"""
        from src.repository.data_repo import DataRepository
        from src.services.data_service import DataService

        mock_check_hash.return_value = False

        mock_loader_instance = MagicMock()
        mock_doc = Document(page_content="Web content", metadata={})
        mock_loader_instance.load.return_value = [mock_doc]
        mock_web_loader.return_value = mock_loader_instance

        mock_store = MagicMock()
        mock_vector_store.return_value = mock_store

        repo = DataRepository()
        service = DataService(repo=repo)
        result = service.add_web_content_as_embedding(
            "https://example.com/article", user_id=1
        )

        assert "added successfully" in result

    @patch("src.repository.data_repo.DataRepository.check_existing_hash")
    def test_add_web_content_duplicate(self, mock_check_hash):
        """Test adding duplicate web content"""
        from src.repository.data_repo import DataRepository
        from src.services.data_service import DataService

        mock_check_hash.return_value = True

        repo = DataRepository()
        service = DataService(repo=repo)
        result = service.add_web_content_as_embedding(
            "https://example.com/duplicate", user_id=1
        )

        assert "already exists" in result

    def test_get_base_url(self):
        """Test base URL extraction"""
        from src.services.data_utility import get_base_url

        url_with_fragment = "https://example.com/page#section"
        base = get_base_url(url_with_fragment)

        assert base == "https://example.com/page"
        assert "#" not in base

    def test_get_base_url_no_fragment(self):
        """Test base URL without fragment"""
        from src.services.data_utility import get_base_url

        url = "https://example.com/page"
        base = get_base_url(url)

        assert base == "https://example.com/page"

    def test_add_metadata_to_documents(self):
        """Test adding metadata to document list"""
        from src.services.data_utility import add_base_url_hash_user_id_to_metadata

        docs = [
            Document(page_content="Doc 1", metadata={}),
            Document(page_content="Doc 2", metadata={}),
        ]

        add_base_url_hash_user_id_to_metadata(
            base_url="https://example.com", hash="abc123", user_id=42, data=docs
        )

        # Check metadata was added
        for doc in docs:
            assert doc.metadata["source"] == "https://example.com"
            assert doc.metadata["hash"] == "abc123"
            assert doc.metadata["user_id"] == 42


class TestHashChecking:
    """Tests for hash existence checking"""

    @patch("src.repository.data_repo.psycopg.connect")
    def test_check_existing_hash_found(self, mock_connect):
        """Test checking hash that exists"""
        from src.repository.data_repo import DataRepository

        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("row1",)]

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=None)

        mock_connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_connect.return_value.__exit__ = MagicMock(return_value=None)

        repo = DataRepository()
        result = repo.check_existing_hash("existing_hash")

        assert result is True

    @patch("src.repository.data_repo.psycopg.connect")
    def test_check_existing_hash_not_found(self, mock_connect):
        """Test checking hash that doesn't exist"""
        from src.repository.data_repo import DataRepository

        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=None)

        mock_connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_connect.return_value.__exit__ = MagicMock(return_value=None)

        repo = DataRepository()
        result = repo.check_existing_hash("nonexistent_hash")

        assert result is False

    @patch("src.repository.data_repo.psycopg.connect")
    def test_check_existing_hash_connection_error(self, mock_connect):
        """Test hash check with connection error"""
        from src.repository.data_repo import DataRepository

        mock_connect.side_effect = Exception("Connection failed")

        repo = DataRepository()
        result = repo.check_existing_hash("any_hash")

        # Should return False on error
        assert result is False
