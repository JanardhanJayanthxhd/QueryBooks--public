from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import status


class TestAIQuery:
    """Tests for AI query endpoint"""

    def test_ai_query_success(self, client):
        """Test successful AI query"""
        from src.api.main import app
        from src.factory.ai_service_factory import get_ai_service

        mock_service = MagicMock()
        mock_service.interact = AsyncMock(
            return_value=("This is an AI generated response", "0.001")
        )
        app.dependency_overrides[get_ai_service] = lambda: mock_service

        query_data = {"query": "What is the meaning of life?"}
        response = client.post("/ai/query", json=query_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["response"] == "success"
        assert "ai response" in data["message"]
        assert "token cost" in data["message"]
        assert len(data["message"]["ai response"]) > 0

    def test_ai_query_with_markdown_cleanup(self, client):
        """Test that AI response markdown is cleaned"""
        from src.api.main import app
        from src.factory.ai_service_factory import get_ai_service

        mock_service = MagicMock()
        mock_service.interact = AsyncMock(
            return_value=("**Bold text** and *italic* with \\backslashes", "0.001")
        )
        app.dependency_overrides[get_ai_service] = lambda: mock_service

        query_data = {"query": "Test query"}
        response = client.post("/ai/query", json=query_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Check that markdown and special characters are cleaned
        ai_response = data["message"]["ai response"]
        assert "**" not in ai_response
        assert "*" not in ai_response
        assert "\\" not in ai_response

    def test_ai_query_empty_query(self, client):
        """Test AI query with empty string"""
        query_data = {"query": ""}
        response = client.post("/ai/query", json=query_data)

        # Should reject empty queries due to validation
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_ai_query_missing_query_field(self, client):
        """Test AI query without query field"""
        response = client.post("/ai/query", json={})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_ai_query_agent_error(self, client):
        """Test AI query when agent raises error"""
        from src.api.main import app
        from src.factory.ai_service_factory import get_ai_service

        mock_service = MagicMock()
        mock_service.interact = AsyncMock(side_effect=Exception("OpenAI API error"))
        app.dependency_overrides[get_ai_service] = lambda: mock_service

        query_data = {"query": "What is AI?"}
        response = client.post("/ai/query", json=query_data)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Error while processing AI query" in response.json()["detail"]

    def test_ai_query_token_cost_calculation(self, client):
        """Test that token cost is included in response"""
        from src.api.main import app
        from src.factory.ai_service_factory import get_ai_service

        mock_service = MagicMock()
        mock_service.interact = AsyncMock(return_value=("Response", "0.001"))
        app.dependency_overrides[get_ai_service] = lambda: mock_service

        query_data = {"query": "Calculate tokens"}
        response = client.post("/ai/query", json=query_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Token cost should be present
        assert "token cost" in data["message"]
        assert data["message"]["token cost"] == "0.001"

    def test_ai_query_long_input(self, client):
        """Test AI query with very long input"""
        from src.api.main import app
        from src.factory.ai_service_factory import get_ai_service

        mock_service = MagicMock()
        mock_service.interact = AsyncMock(
            return_value=("Response to long query", "0.005")
        )
        app.dependency_overrides[get_ai_service] = lambda: mock_service

        long_query = "What is " + ("very " * 1000) + "long?"
        query_data = {"query": long_query}
        response = client.post("/ai/query", json=query_data)

        assert response.status_code == status.HTTP_200_OK


class TestAIQueryUtils:
    """Tests for AI utility functions"""

    @patch("src.factory.agent_factory.ChatOpenAI")
    def test_get_agent_initialization(self, mock_chat_openai):
        """Test that get_agent initializes ChatOpenAI correctly"""
        from src.factory.agent_factory import get_agent

        mock_instance = MagicMock()
        mock_chat_openai.return_value = mock_instance

        agent = get_agent()

        # Verify ChatOpenAI was called with correct parameters
        mock_chat_openai.assert_called_once()
        call_kwargs = mock_chat_openai.call_args.kwargs
        assert call_kwargs["model"] == "gpt-4o-mini"
        assert call_kwargs["temperature"] == 0
        assert call_kwargs["stream_usage"] is True

    def test_calculate_token_cost(self):
        """Test token cost calculation"""
        from src.services.ai_utility import calculate_token_cost

        token_usage = {"input_tokens": 1000, "output_tokens": 500}

        cost = calculate_token_cost(token_usage, model_name="gpt-4o-mini")

        # Cost should be a string representation of a decimal
        assert isinstance(cost, str)
        assert float(cost) > 0

    def test_clean_llm_output(self):
        """Test LLM output cleaning"""
        from src.core.utility import clean_llm_output

        dirty_text = "**Bold** text with *italics* and \\backslashes  extra   spaces"
        cleaned = clean_llm_output(dirty_text)

        # Check markdown and special chars are removed
        assert "**" not in cleaned
        assert "*" not in cleaned
        assert "\\" not in cleaned

        # Check extra whitespace is normalized
        assert "  " not in cleaned

    def test_update_history(self):
        """Test conversation history update"""
        from src.core.constants import HISTORY
        from src.services.ai_utility import update_history

        # Clear history
        HISTORY.clear()

        update_history("AI response", "User question")

        # History should contain both messages
        assert len(HISTORY) == 2
        assert HISTORY[0].content == "User question"
        assert HISTORY[1].content == "AI response"
