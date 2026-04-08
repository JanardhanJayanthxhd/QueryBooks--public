import json

from fastapi import status


class TestUserRegistration:
    """Tests for user registration endpoint"""

    def test_register_new_user_success(self, client, test_user_data):
        """Test successful user registration"""
        response = client.post("/user/register", json=test_user_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["response"] == "success"
        assert "user details" in data["message"]
        assert data["message"]["user details"]["email"] == test_user_data["email"]
        assert data["message"]["user details"]["name"] == test_user_data["name"]

    def test_register_duplicate_user_fails(self, client, test_user, test_user_data):
        """Test that registering with existing email fails"""
        response = client.post("/user/register", json=test_user_data)
        # ExistingUserException is caught by route and re-raised as 500
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_register_user_invalid_data(self, client):
        """Test registration with invalid data"""
        invalid_data = {
            "name": "Test",
            "email": "not-an-email",
            # Missing password
        }
        response = client.post("/user/register", json=invalid_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_user_missing_fields(self, client):
        """Test registration with missing required fields"""
        incomplete_data = {
            "name": "Test User"
            # Missing email and password
        }
        response = client.post("/user/register", json=incomplete_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestUserLogin:
    """Tests for user login endpoint"""

    def test_login_success(self, client, test_user, test_user_data):
        """Test successful user login"""
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"],
        }
        response = client.post("/user/login", json=login_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["response"] == "success"
        assert "token" in data["message"]
        assert len(data["message"]["token"]) > 0

    def test_login_wrong_password(self, client, test_user, test_user_data):
        """Test login with incorrect password"""
        login_data = {"email": test_user_data["email"], "password": "wrongpassword"}
        response = client.post("/user/login", json=login_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid email or password" in response.json()["detail"]

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user"""
        login_data = {"email": "nonexistent@example.com", "password": "somepassword"}
        response = client.post("/user/login", json=login_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Unable to find user" in response.json()["detail"]

    def test_login_invalid_data(self, client):
        """Test login with invalid data format"""
        invalid_data = {
            "email": "not-an-email",
            # Missing password
        }
        response = client.post("/user/login", json=invalid_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_login_empty_credentials(self, client):
        """Test login with empty credentials"""
        empty_data = {"email": "", "password": ""}
        response = client.post("/user/login", json=empty_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestUserAuthentication:
    """Tests for JWT authentication"""

    def test_valid_token_authentication(self, client, test_user, auth_headers):
        """Test that valid token allows access to protected endpoints"""
        # Using the chat endpoint as it requires authentication
        query_data = {"query": "test query"}
        response = client.post("/chat", json=query_data, headers=auth_headers)

        # Should not get 401 Unauthorized
        assert response.status_code != status.HTTP_401_UNAUTHORIZED

    def test_missing_token_fails(self, client):
        """Test that missing token returns 401"""
        query_data = {"query": "test query"}
        response = client.post("/chat", json=query_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_invalid_token_fails(self, client):
        """Test that invalid token returns 401"""
        invalid_headers = {"Authorization": "Bearer invalid_token_here"}
        query_data = {"query": "test query"}
        response = client.post("/chat", json=query_data, headers=invalid_headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_malformed_auth_header_fails(self, client):
        """Test that malformed authorization header fails"""
        malformed_headers = {"Authorization": "InvalidFormat token"}
        query_data = {"query": "test query"}
        response = client.post("/chat", json=query_data, headers=malformed_headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
