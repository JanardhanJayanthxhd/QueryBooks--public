from io import BytesIO
from unittest.mock import MagicMock, patch

from fastapi import status
from langchain_core.documents import Document


class TestPDFUpload:
    """Tests for PDF file upload endpoint"""

    def test_upload_pdf_success(self, client, auth_headers, mock_pdf_file):
        """Test successful PDF upload"""
        from src.api.main import app
        from src.api.routes.data import get_data_service

        mock_service = MagicMock()
        mock_service.add_pdf_as_embedding.return_value = (
            "File - test.pdf - added successfully"
        )
        app.dependency_overrides[get_data_service] = lambda: mock_service

        files = {"file": ("test.pdf", BytesIO(mock_pdf_file), "application/pdf")}
        response = client.post("/data/upload_pdf", files=files, headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["response"] == "success"
        assert "added successfully" in data["message"]["db response"]

    def test_upload_duplicate_pdf(self, client, auth_headers, mock_pdf_file):
        """Test uploading duplicate PDF returns appropriate message"""
        from src.api.main import app
        from src.api.routes.data import get_data_service

        mock_service = MagicMock()
        mock_service.add_pdf_as_embedding.return_value = (
            "File - duplicate.pdf - already exists"
        )
        app.dependency_overrides[get_data_service] = lambda: mock_service

        files = {"file": ("duplicate.pdf", BytesIO(mock_pdf_file), "application/pdf")}
        response = client.post("/data/upload_pdf", files=files, headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "already exists" in data["message"]["db response"]

    def test_upload_non_pdf_file_fails(self, client, auth_headers):
        """Test that non-PDF files are rejected"""
        txt_content = b"This is a text file"
        files = {"file": ("test.txt", BytesIO(txt_content), "text/plain")}
        response = client.post("/data/upload_pdf", files=files, headers=auth_headers)

        assert response.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE

    def test_upload_pdf_without_auth_fails(self, client, mock_pdf_file):
        """Test that PDF upload without authentication fails"""
        files = {"file": ("test.pdf", BytesIO(mock_pdf_file), "application/pdf")}
        response = client.post("/data/upload_pdf", files=files)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_upload_pdf_missing_file(self, client, auth_headers):
        """Test upload without file fails"""
        response = client.post("/data/upload_pdf", headers=auth_headers)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_upload_pdf_processing_error(self, client, auth_headers, mock_pdf_file):
        """Test PDF upload with processing error"""
        from src.api.main import app
        from src.api.routes.data import get_data_service

        mock_service = MagicMock()
        mock_service.add_pdf_as_embedding.side_effect = Exception("Processing error")
        app.dependency_overrides[get_data_service] = lambda: mock_service

        files = {"file": ("test.pdf", BytesIO(mock_pdf_file), "application/pdf")}
        response = client.post("/data/upload_pdf", files=files, headers=auth_headers)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Error while uploading file" in response.json()["detail"]


class TestWebContentUpload:
    """Tests for web content upload endpoint"""

    def test_upload_web_content_success(self, client, auth_headers):
        """Test successful web content upload"""
        from src.api.main import app
        from src.api.routes.data import get_data_service

        mock_service = MagicMock()
        mock_service.add_web_content_as_embedding.return_value = (
            "web - https://example.com/article - added successfully"
        )
        app.dependency_overrides[get_data_service] = lambda: mock_service

        url_data = {"url": "https://example.com/article"}
        response = client.post(
            "/data/upload_web_content", json=url_data, headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["response"] == "success"
        assert "added successfully" in data["message"]["db response"]

    def test_upload_duplicate_web_content(self, client, auth_headers):
        """Test uploading duplicate web content"""
        from src.api.main import app
        from src.api.routes.data import get_data_service

        mock_service = MagicMock()
        mock_service.add_web_content_as_embedding.return_value = (
            "web - https://example.com/article - already exists"
        )
        app.dependency_overrides[get_data_service] = lambda: mock_service

        url_data = {"url": "https://example.com/article"}
        response = client.post(
            "/data/upload_web_content", json=url_data, headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "already exists" in data["message"]["db response"]

    def test_upload_web_content_without_auth_fails(self, client):
        """Test web content upload without authentication fails"""
        url_data = {"url": "https://example.com/article"}
        response = client.post("/data/upload_web_content", json=url_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_upload_web_content_invalid_url(self, client, auth_headers):
        """Test web content upload with invalid URL format"""
        invalid_url_data = {"url": "not-a-valid-url"}
        response = client.post(
            "/data/upload_web_content", json=invalid_url_data, headers=auth_headers
        )

        # Pydantic validation should catch this
        assert response.status_code in [
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]

    def test_upload_web_content_missing_url(self, client, auth_headers):
        """Test web content upload without URL"""
        response = client.post(
            "/data/upload_web_content", json={}, headers=auth_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_upload_web_content_fetch_error(self, client, auth_headers):
        """Test web content upload with fetch error"""
        from src.api.main import app
        from src.api.routes.data import get_data_service

        mock_service = MagicMock()
        mock_service.add_web_content_as_embedding.side_effect = Exception(
            "Failed to fetch"
        )
        app.dependency_overrides[get_data_service] = lambda: mock_service

        url_data = {"url": "https://example.com/article"}
        response = client.post(
            "/data/upload_web_content", json=url_data, headers=auth_headers
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Error while uploading web content" in response.json()["detail"]

    def test_upload_web_content_with_fragment(self, client, auth_headers):
        """Test that URL fragments are handled correctly"""
        from src.api.main import app
        from src.api.routes.data import get_data_service

        mock_service = MagicMock()
        mock_service.add_web_content_as_embedding.return_value = (
            "web - https://example.com/page - added successfully"
        )
        app.dependency_overrides[get_data_service] = lambda: mock_service

        # URL with fragment identifier
        url_data = {"url": "https://example.com/page#section"}
        response = client.post(
            "/data/upload_web_content", json=url_data, headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
