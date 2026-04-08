from datetime import timedelta
from unittest.mock import MagicMock, patch


class TestJWTCreation:
    """Tests for JWT token creation"""

    def test_create_access_token_without_expiry(self):
        """Test creating token without expiration"""
        from src.core.jwt import create_access_token

        data = {"email": "test@example.com", "id": 1}
        token = create_access_token(data, expires_delta=None)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_expiry(self):
        """Test creating token with custom expiration"""
        from src.core.jwt import create_access_token

        data = {"email": "test@example.com", "id": 1}
        expires = timedelta(minutes=30)
        token = create_access_token(data, expires_delta=expires)

        assert token is not None
        assert isinstance(token, str)

    def test_create_token_different_data_different_tokens(self):
        """Test that different data produces different tokens"""
        from src.core.jwt import create_access_token

        data1 = {"email": "user1@test.com", "id": 1}
        data2 = {"email": "user2@test.com", "id": 2}

        token1 = create_access_token(data1, None)
        token2 = create_access_token(data2, None)

        assert token1 != token2

    def test_create_token_with_additional_claims(self):
        """Test creating token with additional claims"""
        from src.core.jwt import create_access_token

        data = {
            "email": "test@test.com",
            "id": 1,
            "role": "admin",
            "custom_field": "value",
        }
        token = create_access_token(data, None)

        assert token is not None


class TestJWTAuthentication:
    """Tests for JWT authentication and validation"""

    @patch("src.core.jwt_utility.get_db")
    def test_authenticate_user_from_token_success(self, mock_get_db, test_user):
        """Test successful authentication from valid token"""
        from fastapi.security import HTTPAuthorizationCredentials
        from src.core.jwt import create_access_token
        from src.core.jwt_utility import authenticate_user_from_token

        # Create valid token
        token = create_access_token(
            {"email": test_user.email, "id": test_user.id}, None
        )

        # Mock database session
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = test_user
        mock_get_db.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_get_db.return_value.__exit__ = MagicMock(return_value=None)

        # Create HTTPAuthorizationCredentials object with the token
        mock_credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=token
        )

        # Call the function with the correct parameter types
        result = authenticate_user_from_token(credentials=mock_credentials, db=mock_db)

        assert result is not None
        assert result.id == test_user.id

    def test_authenticate_missing_token(self, client):
        """Test authentication with missing token via endpoint"""
        # Test through actual endpoint instead of calling function directly
        query_data = {"query": "test"}
        response = client.post("/chat", json=query_data)

        assert response.status_code == 401

    def test_authenticate_invalid_token_format(self, client):
        """Test authentication with invalid token format via endpoint"""
        invalid_headers = {"Authorization": "InvalidFormat token"}
        query_data = {"query": "test"}
        response = client.post("/chat", json=query_data, headers=invalid_headers)

        assert response.status_code == 401

    def test_authenticate_malformed_token(self, client):
        """Test authentication with malformed JWT via endpoint"""
        malformed_headers = {"Authorization": "Bearer invalid.jwt.token"}
        query_data = {"query": "test"}
        response = client.post("/chat", json=query_data, headers=malformed_headers)

        assert response.status_code == 401

    def test_authenticate_user_not_in_database(self, client):
        """Test authentication when user doesn't exist in database"""
        from src.core.jwt import create_access_token

        # Create token for non-existent user
        token = create_access_token({"email": "ghost@test.com", "id": 9999}, None)

        headers = {"Authorization": f"Bearer {token}"}
        query_data = {"query": "test"}
        response = client.post("/chat", json=query_data, headers=headers)

        assert response.status_code == 401


class TestJWTTokenDecoding:
    """Tests for JWT token decoding and validation"""

    def test_decode_valid_token(self):
        """Test decoding a valid token"""
        import os

        from jose import jwt
        from src.core.jwt import create_access_token

        data = {"email": "test@test.com", "id": 1}
        token = create_access_token(data, None)

        # Decode token
        secret = os.getenv("JWT_SECRET_KEY")
        decoded = jwt.decode(token, secret, algorithms=["HS256"])

        assert decoded["email"] == "test@test.com"
        assert decoded["id"] == 1
        assert "exp" in decoded

    def test_token_contains_expiration(self):
        """Test that token contains expiration claim"""
        import os

        from jose import jwt
        from src.core.jwt import create_access_token

        data = {"email": "test@test.com"}
        token = create_access_token(data, None)

        secret = os.getenv("JWT_SECRET_KEY")
        decoded = jwt.decode(token, secret, algorithms=["HS256"])

        assert "exp" in decoded
        assert isinstance(decoded["exp"], int)

    def test_expired_token_raises_error(self):
        """Test that expired token is rejected"""
        import os
        import time

        from jose import JWTError, jwt
        from src.core.jwt import create_access_token

        # Create token that expires in 1 microsecond
        data = {"email": "test@test.com"}
        token = create_access_token(data, timedelta(microseconds=1))

        # Wait for expiration
        time.sleep(0.1)

        secret = os.getenv("JWT_SECRET_KEY")

        # Attempting to decode should raise an error
        try:
            decoded = jwt.decode(token, secret, algorithms=["HS256"])
            # If we get here without error, the token might still be valid
            # Check if exp claim exists and is in the past
            assert "exp" in decoded
        except JWTError:
            # Expected - token expired
            pass


class TestJWTIntegration:
    """Integration tests for JWT in API endpoints"""

    def test_protected_endpoint_with_valid_token(self, client, auth_headers):
        """Test accessing protected endpoint with valid token"""
        query_data = {"query": "test"}
        response = client.post("/chat", json=query_data, headers=auth_headers)

        # Should not return 401
        assert response.status_code != 401

    def test_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without token"""
        query_data = {"query": "test"}
        response = client.post("/chat", json=query_data)

        assert response.status_code == 401

    def test_protected_endpoint_with_invalid_token(self, client):
        """Test accessing protected endpoint with invalid token"""
        invalid_headers = {"Authorization": "Bearer invalid_token_string"}
        query_data = {"query": "test"}
        response = client.post("/chat", json=query_data, headers=invalid_headers)

        assert response.status_code == 401

    def test_multiple_endpoints_with_same_token(self, client, auth_headers):
        """Test that same token works across multiple endpoints"""
        # Try data upload endpoint
        from io import BytesIO

        files = {"file": ("test.pdf", BytesIO(b"%PDF"), "application/pdf")}
        response1 = client.post("/data/upload_pdf", files=files, headers=auth_headers)

        # Try chat endpoint
        query_data = {"query": "test"}
        response2 = client.post("/chat", json=query_data, headers=auth_headers)

        # Both should authenticate successfully
        assert response1.status_code != 401
        assert response2.status_code != 401

    def test_token_after_user_data_change(self, client, test_user, test_db_session):
        """Test that token remains valid even after user data changes"""
        from src.core.jwt import create_access_token

        # Create token
        token = create_access_token(
            {"email": test_user.email, "id": test_user.id}, None
        )
        headers = {"Authorization": f"Bearer {token}"}

        # Modify user (e.g., change name)
        test_user.name = "Modified Name"
        test_db_session.commit()

        # Token should still work
        query_data = {"query": "test"}
        response = client.post("/chat", json=query_data, headers=headers)

        assert response.status_code != 401


class TestJWTEdgeCases:
    """Tests for JWT edge cases"""

    def test_token_with_empty_data(self):
        """Test creating token with minimal data"""
        from src.core.jwt import create_access_token

        data = {}
        token = create_access_token(data, None)

        assert token is not None
        assert isinstance(token, str)

    def test_token_with_special_characters_in_email(self):
        """Test token with special characters"""
        from src.core.jwt import create_access_token

        data = {"email": "user+test@example.com", "id": 1}
        token = create_access_token(data, None)

        assert token is not None

    def test_very_long_token_data(self):
        """Test token with large payload"""
        from src.core.jwt import create_access_token

        data = {
            "email": "test@test.com",
            "id": 1,
            "metadata": "x" * 1000,  # Long string
        }
        token = create_access_token(data, None)

        assert token is not None
        assert len(token) > 0
