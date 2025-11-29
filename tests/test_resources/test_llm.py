import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.resources.llm import LLMClient
from langchain_core.messages import AIMessage
from app.config.settings import settings


class TestLLMClient:
    def test_init_openai(self, mocker):
        """Test initialization with OpenAI provider."""
        mock_settings = MagicMock()
        mock_settings.LLM_PROVIDER = settings.LLM_PROVIDER
        mock_settings.LLM_MODEL = settings.LLM_MODEL
        mock_settings.LLM_API_KEY = settings.LLM_API_KEY
        mock_settings.LLM_BASE_URL = settings.LLM_BASE_URL
        mock_settings.LLM_TEMPERATURE = settings.LLM_TEMPERATURE
        mocker.patch("app.resources.llm.settings", mock_settings)

        mock_chat_openai = MagicMock()
        with patch("langchain_openai.ChatOpenAI", return_value=mock_chat_openai):
            client = LLMClient()

        assert client.provider == settings.LLM_PROVIDER
        assert client.model == settings.LLM_MODEL
        assert client.api_key == settings.LLM_API_KEY
        assert client.base_url == settings.LLM_BASE_URL
        assert client.client == mock_chat_openai

    def test_init_openai_with_params(self, mocker):
        """Test initialization with custom parameters."""
        mock_settings = MagicMock()
        mocker.patch("app.resources.llm.settings", mock_settings)

        mock_chat_openai = MagicMock()
        with patch("langchain_openai.ChatOpenAI", return_value=mock_chat_openai):
            client = LLMClient(
                provider=settings.LLM_PROVIDER,
                model=settings.LLM_MODEL,
                api_key=settings.SECRET_KEY,
                base_url=settings.LLM_BASE_URL,
            )

        assert client.provider == settings.LLM_PROVIDER
        assert client.model == settings.LLM_MODEL
        assert client.api_key == settings.SECRET_KEY
        assert client.base_url == settings.LLM_BASE_URL

    def test_init_unsupported_provider(self, mocker):
        """Test initialization with unsupported provider."""
        mock_settings = MagicMock()
        mocker.patch("app.resources.llm.settings", mock_settings)

        with pytest.raises(ValueError, match="Unsupported provider: unsupported"):
            LLMClient(provider="unsupported")

    @pytest.mark.asyncio
    async def test_chat_openai_success(self, mocker):
        """Test successful OpenAI chat completion."""
        mock_settings = MagicMock()
        mock_settings.LLM_TEMPERATURE = 0.1
        mocker.patch("app.resources.llm.settings", mock_settings)

        mock_client = AsyncMock()
        mock_response = AIMessage(content="Hello world")
        mock_client.ainvoke.return_value = mock_response

        with patch("langchain_openai.ChatOpenAI", return_value=mock_client):
            client = LLMClient(provider="openai")

        messages = [{"role": "user", "content": "Hello"}]
        result = await client.chat(messages)

        assert result == mock_response
        mock_client.ainvoke.assert_called_once_with(messages, temperature=0.1)

    @pytest.mark.asyncio
    async def test_chat_openai_with_tools(self, mocker):
        """Test OpenAI chat with tools."""
        mock_settings = MagicMock()
        mock_settings.LLM_TEMPERATURE = 0.1
        mocker.patch("app.resources.llm.settings", mock_settings)

        mock_client = AsyncMock()
        mock_bound_client = AsyncMock()
        mock_client.bind_tools = MagicMock(return_value=mock_bound_client)
        mock_response = AIMessage(content="Tool response")
        mock_bound_client.ainvoke.return_value = mock_response

        with patch("langchain_openai.ChatOpenAI", return_value=mock_client):
            client = LLMClient(provider="openai")

        messages = [{"role": "user", "content": "Use tool"}]
        tools = [{"name": "test_tool"}]
        result = await client.chat(messages, tools=tools)

        assert result == mock_response
        mock_client.bind_tools.assert_called_once_with(tools)
        mock_bound_client.ainvoke.assert_called_once_with(messages, temperature=0.1)

    @pytest.mark.asyncio
    async def test_chat_openai_with_custom_params(self, mocker):
        """Test OpenAI chat with custom temperature and max_tokens."""
        mock_settings = MagicMock()
        mock_settings.LLM_TEMPERATURE = 0.1
        mocker.patch("app.resources.llm.settings", mock_settings)

        mock_client = AsyncMock()
        mock_response = AIMessage(content="Custom response")
        mock_client.ainvoke.return_value = mock_response

        with patch("langchain_openai.ChatOpenAI", return_value=mock_client):
            client = LLMClient(provider="openai")

        messages = [{"role": "user", "content": "Hello"}]
        result = await client.chat(messages, temperature=0.5, max_tokens=100)

        assert result == mock_response
        mock_client.ainvoke.assert_called_once_with(
            messages, temperature=0.5, max_tokens=100
        )
