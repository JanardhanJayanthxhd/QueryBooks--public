from unittest.mock import MagicMock, patch

from src.core.utility import CacheDetails
from src.models.cache import UserLLMCache


class TestCaching:
    """Tests for LLM response caching functionality"""

    def test_save_to_cache_success(self, test_db_session, test_user):
        """Test saving a response to cache"""
        from src.core.constants import settings
        from src.repository.cache_repo import CacheRepository
        from src.services.cache_service import CacheService

        service = CacheService(repo=CacheRepository(session=test_db_session))
        details = CacheDetails(user_id=test_user.id, question="What is AI?")
        response = "Artificial Intelligence is..."

        service.save_to_cache(details, response)

        # Verify cache entry was created
        cached = (
            test_db_session.query(UserLLMCache)
            .filter_by(user_id=test_user.id, prompt="What is AI?")
            .first()
        )

        assert cached is not None
        assert cached.response == response
        assert cached.llm == settings.LLM_NAME

    def test_get_cached_response_exists(self, test_db_session, test_user):
        """Test retrieving an existing cached response"""
        from src.repository.cache_repo import CacheRepository
        from src.services.cache_service import CacheService

        service = CacheService(repo=CacheRepository(session=test_db_session))
        details = CacheDetails(user_id=test_user.id, question="Cached question")
        expected_response = "Cached answer"

        # Save to cache first
        service.save_to_cache(details, expected_response)

        # Retrieve from cache
        cached_response = service.get_cached_response(details)

        assert cached_response == expected_response

    def test_get_cached_response_not_exists(self, test_db_session, test_user):
        """Test retrieving non-existent cached response returns None"""
        from src.repository.cache_repo import CacheRepository
        from src.services.cache_service import CacheService

        service = CacheService(repo=CacheRepository(session=test_db_session))
        details = CacheDetails(user_id=test_user.id, question="Never asked before")

        cached_response = service.get_cached_response(details)

        assert cached_response is None

    def test_cache_user_isolation(self, test_db_session):
        """Test that cache is isolated per user"""
        from src.core.utility import hash_password
        from src.models.user import User
        from src.repository.cache_repo import CacheRepository
        from src.services.cache_service import CacheService

        # Create two users
        user1 = User(
            name="User One",
            email="user1@test.com",
            password_hash=hash_password("pass1"),
        )
        user2 = User(
            name="User Two",
            email="user2@test.com",
            password_hash=hash_password("pass2"),
        )
        test_db_session.add_all([user1, user2])
        test_db_session.commit()
        test_db_session.refresh(user1)
        test_db_session.refresh(user2)

        same_question = "What is the capital of France?"

        service = CacheService(repo=CacheRepository(session=test_db_session))

        # User 1 caches a response
        details1 = CacheDetails(user_id=user1.id, question=same_question)
        service.save_to_cache(details1, "Paris (User 1's answer)")

        # User 2 should not get User 1's cache
        details2 = CacheDetails(user_id=user2.id, question=same_question)
        cached_for_user2 = service.get_cached_response(details2)

        assert cached_for_user2 is None

    def test_cache_different_questions_same_user(self, test_db_session, test_user):
        """Test that different questions are cached separately"""
        from src.repository.cache_repo import CacheRepository
        from src.services.cache_service import CacheService

        service = CacheService(repo=CacheRepository(session=test_db_session))

        # Cache two different questions
        details1 = CacheDetails(user_id=test_user.id, question="Question 1")
        service.save_to_cache(details1, "Answer 1")

        details2 = CacheDetails(user_id=test_user.id, question="Question 2")
        service.save_to_cache(details2, "Answer 2")

        # Retrieve and verify
        response1 = service.get_cached_response(details1)
        response2 = service.get_cached_response(details2)

        assert response1 == "Answer 1"
        assert response2 == "Answer 2"

    def test_cache_with_special_characters(self, test_db_session, test_user):
        """Test caching with special characters in question"""
        from src.repository.cache_repo import CacheRepository
        from src.services.cache_service import CacheService

        special_question = "What's the meaning of life? (42!)"

        service = CacheService(repo=CacheRepository(session=test_db_session))
        details = CacheDetails(user_id=test_user.id, question=special_question)
        service.save_to_cache(details, "42 is the answer")

        cached = service.get_cached_response(details)
        assert cached == "42 is the answer"

    def test_cache_with_long_response(self, test_db_session, test_user):
        """Test caching with very long response"""
        from src.repository.cache_repo import CacheRepository
        from src.services.cache_service import CacheService

        long_response = "A" * 10000  # 10K characters

        service = CacheService(repo=CacheRepository(session=test_db_session))
        details = CacheDetails(user_id=test_user.id, question="Long response test")
        service.save_to_cache(details, long_response)

        cached = service.get_cached_response(details)
        assert cached == long_response
        assert len(cached) == 10000


class TestCacheIntegration:
    """Integration tests for caching with API endpoints"""

    def test_chat_uses_cache_on_second_call(
        self, client, auth_headers, test_db_session
    ):
        """Test that second identical query uses cache"""
        from src.api.main import app
        from src.factory.ai_service_factory import get_ai_service

        mock_ai_svc = MagicMock()
        mock_ai_svc.chat.return_value = ("First response", "0.001")
        app.dependency_overrides[get_ai_service] = lambda: mock_ai_svc

        query_data = {"query": "Repeated question"}

        # First call - should invoke AI
        response1 = client.post("/chat", json=query_data, headers=auth_headers)
        assert response1.status_code == 200
        assert "token cost" in response1.json()["message"]

        # Second call - should use cache
        response2 = client.post("/chat", json=query_data, headers=auth_headers)
        assert response2.status_code == 200

        # Cache response shouldn't have token cost
        assert "token cost" not in response2.json()["message"]

        # AI should only be invoked once
        assert mock_ai_svc.chat.call_count == 1

    def test_different_users_dont_share_cache(self, client, test_db_session):
        """Test that different users have separate caches"""
        from src.api.main import app
        from src.core.jwt import create_access_token
        from src.core.utility import hash_password
        from src.factory.ai_service_factory import get_ai_service
        from src.models.user import User

        # Create two users
        user1 = User(
            name="Alice", email="alice@test.com", password_hash=hash_password("pass1")
        )
        user2 = User(
            name="Bob", email="bob@test.com", password_hash=hash_password("pass2")
        )
        test_db_session.add_all([user1, user2])
        test_db_session.commit()
        test_db_session.refresh(user1)
        test_db_session.refresh(user2)

        # Generate tokens
        token1 = create_access_token({"email": user1.email, "id": user1.id}, None)
        token2 = create_access_token({"email": user2.email, "id": user2.id}, None)

        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}

        mock_ai_svc = MagicMock()
        mock_ai_svc.chat.return_value = ("Response", "0.001")
        app.dependency_overrides[get_ai_service] = lambda: mock_ai_svc

        query_data = {"query": "Same question"}

        # User 1 makes query
        response1 = client.post("/chat", json=query_data, headers=headers1)
        assert response1.status_code == 200

        # User 2 makes same query - should NOT use User 1's cache
        response2 = client.post("/chat", json=query_data, headers=headers2)
        assert response2.status_code == 200

        # AI should be invoked twice (once per user)
        assert mock_ai_svc.chat.call_count == 2
