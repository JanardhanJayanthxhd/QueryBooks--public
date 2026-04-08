from unittest.mock import MagicMock, patch

from fastapi import status
from langchain_core.documents import Document


class TestChatEndpoint:
    """Tests for chat endpoint with RAG"""

    def test_chat_query_success(self, client, auth_headers, test_user):
        """Test successful chat query with RAG"""
        from src.api.main import app
        from src.api.routes.chat import get_cache_service
        from src.factory.ai_service_factory import get_ai_service

        mock_cache_svc = MagicMock()
        mock_cache_svc.get_cached_response.return_value = None
        app.dependency_overrides[get_cache_service] = lambda: mock_cache_svc

        mock_ai_svc = MagicMock()
        mock_ai_svc.chat.return_value = (
            "Based on your documents, the answer is...",
            "0.001",
        )
        app.dependency_overrides[get_ai_service] = lambda: mock_ai_svc

        query_data = {"query": "What does my document say?"}
        response = client.post("/chat", json=query_data, headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["response"] == "success"
        assert "query response" in data["message"]
        assert "token cost" in data["message"]
        assert "response time" in data["message"]

    def test_chat_query_from_cache(self, client, auth_headers):
        """Test chat query returns cached response"""
        from src.api.main import app
        from src.api.routes.chat import get_cache_service
        from src.factory.ai_service_factory import get_ai_service

        cached_response = "This is a cached response"
        mock_cache_svc = MagicMock()
        mock_cache_svc.get_cached_response.return_value = cached_response
        app.dependency_overrides[get_cache_service] = lambda: mock_cache_svc
        app.dependency_overrides[get_ai_service] = lambda: MagicMock()

        query_data = {"query": "Cached question"}
        response = client.post("/chat", json=query_data, headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["response"] == "success"
        assert data["message"]["query response"] == cached_response
        assert "response time" in data["message"]
        # Token cost should not be present for cached responses
        assert "token cost" not in data["message"]

    def test_chat_query_without_auth_fails(self, client):
        """Test chat query without authentication"""
        query_data = {"query": "Test query"}
        response = client.post("/chat", json=query_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_chat_query_missing_query_field(self, client, auth_headers):
        """Test chat query without query field"""
        response = client.post("/chat", json={}, headers=auth_headers)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_chat_query_rag_error(self, client, auth_headers):
        """Test chat query when AI service fails"""
        from src.api.main import app
        from src.api.routes.chat import get_cache_service
        from src.factory.ai_service_factory import get_ai_service

        mock_cache_svc = MagicMock()
        mock_cache_svc.get_cached_response.return_value = None
        app.dependency_overrides[get_cache_service] = lambda: mock_cache_svc

        mock_ai_svc = MagicMock()
        mock_ai_svc.chat.side_effect = Exception("RAG error")
        app.dependency_overrides[get_ai_service] = lambda: mock_ai_svc

        query_data = {"query": "Test query"}
        response = client.post("/chat", json=query_data, headers=auth_headers)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Error while chatting with AI" in response.json()["detail"]

    def test_chat_query_saves_to_cache(self, client, auth_headers):
        """Test that successful query saves to cache"""
        from src.api.main import app
        from src.api.routes.chat import get_cache_service
        from src.factory.ai_service_factory import get_ai_service

        mock_cache_svc = MagicMock()
        mock_cache_svc.get_cached_response.return_value = None
        app.dependency_overrides[get_cache_service] = lambda: mock_cache_svc

        mock_ai_svc = MagicMock()
        mock_ai_svc.chat.return_value = ("New response", "0.001")
        app.dependency_overrides[get_ai_service] = lambda: mock_ai_svc

        query_data = {"query": "New query"}
        response = client.post("/chat", json=query_data, headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        # Verify save_to_cache was called on the cache service
        mock_cache_svc.save_to_cache.assert_called_once()

    def test_chat_query_with_long_context(self, client, auth_headers):
        """Test chat query with long document context"""
        from src.api.main import app
        from src.api.routes.chat import get_cache_service
        from src.factory.ai_service_factory import get_ai_service

        mock_cache_svc = MagicMock()
        mock_cache_svc.get_cached_response.return_value = None
        app.dependency_overrides[get_cache_service] = lambda: mock_cache_svc

        mock_ai_svc = MagicMock()
        mock_ai_svc.chat.return_value = (
            "Response based on long documents",
            "0.05",
        )
        app.dependency_overrides[get_ai_service] = lambda: mock_ai_svc

        query_data = {"query": "Summarize all documents"}
        response = client.post("/chat", json=query_data, headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Token cost expected
        token_cost = float(data["message"]["token cost"])
        assert token_cost > 0


class TestRAGChainFunctions:
    """Tests for RAG chain utility functions"""

    @patch("src.services.ai_utility.get_vector_store")
    def test_contextualized_retrieval_without_history(self, mock_vector_store):
        """Test document retrieval without chat history"""
        from src.services.ai_utility import contextualized_retrival

        mock_docs = [
            Document(
                page_content="Test content",
                metadata={"title": "Test Doc", "user_id": 1},
            )
        ]

        mock_store = MagicMock()
        mock_store.similarity_search = MagicMock(return_value=mock_docs)
        mock_vector_store.return_value = mock_store

        input_dict = {"question": "What is this?", "chat_history": [], "user_id": 1}

        result = contextualized_retrival(input_dict)

        # Should return documents
        assert len(result) > 0
        # Should search with original question when no history
        mock_store.similarity_search.assert_called_once()

    @patch("src.services.ai_utility.get_contextualize_rag_chain")
    @patch("src.services.ai_utility.get_vector_store")
    def test_contextualized_retrieval_with_history(
        self, mock_vector_store, mock_contextualize_chain
    ):
        """Test document retrieval with chat history reformulates question"""
        from langchain_core.messages import AIMessage, HumanMessage
        from src.services.ai_utility import contextualized_retrival

        mock_docs = [Document(page_content="Content", metadata={"user_id": 1})]

        mock_store = MagicMock()
        mock_store.similarity_search = MagicMock(return_value=mock_docs)
        mock_vector_store.return_value = mock_store

        mock_chain = MagicMock()
        mock_chain.invoke = MagicMock(return_value="Reformulated question")
        mock_contextualize_chain.return_value = mock_chain

        input_dict = {
            "question": "What about that?",
            "chat_history": [
                HumanMessage(content="Tell me about X"),
                AIMessage(content="X is..."),
            ],
            "user_id": 1,
        }

        result = contextualized_retrival(input_dict)

        # Should call contextualize chain when history exists
        mock_chain.invoke.assert_called_once()
        assert len(result) > 0

    def test_format_docs(self):
        """Test document formatting for LLM"""
        from src.services.ai_utility import format_docs

        docs = [
            Document(
                page_content="First document content", metadata={"title": "Doc 1"}
            ),
            Document(
                page_content="Second document content", metadata={"title": "Doc 2"}
            ),
        ]

        formatted = format_docs(docs)

        # Check formatting includes metadata and content
        assert "DOCUMENT 1" in formatted
        assert "DOCUMENT 2" in formatted
        assert "Metadata Title: Doc 1" in formatted
        assert "Metadata Title: Doc 2" in formatted
        assert "First document content" in formatted
        assert "Second document content" in formatted

    def test_format_docs_unknown_title(self):
        """Test document formatting with missing title metadata"""
        from src.services.ai_utility import format_docs

        docs = [Document(page_content="Content without title", metadata={})]

        formatted = format_docs(docs)

        # Should handle missing title gracefully
        assert "Unknown Title" in formatted
        assert "Content without title" in formatted

    @patch("src.services.ai_utility.get_vector_store")
    def test_contextualized_retrieval_user_filter(self, mock_vector_store):
        """Test that retrieval filters by user_id"""
        from src.services.ai_utility import contextualized_retrival

        mock_docs = [Document(page_content="User doc", metadata={"user_id": 123})]

        mock_store = MagicMock()
        mock_store.similarity_search = MagicMock(return_value=mock_docs)
        mock_vector_store.return_value = mock_store

        input_dict = {"question": "My documents", "chat_history": [], "user_id": 123}

        contextualized_retrival(input_dict)

        # Verify filter was applied
        call_kwargs = mock_store.similarity_search.call_args.kwargs
        assert call_kwargs["filter"] == {"user_id": 123}
