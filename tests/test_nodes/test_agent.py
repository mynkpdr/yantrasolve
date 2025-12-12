"""Tests for app/nodes/agent.py"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from langchain_core.messages import AIMessage, SystemMessage

from app.nodes.agent import agent_node, get_system_prompt


class TestGetSystemPrompt:
    """Test cases for get_system_prompt function."""

    def test_returns_string(self):
        """Test that get_system_prompt returns a string."""
        state = {
            "email": "test@example.com",
            "secret": "test-secret",
            "current_url": "http://example.com/quiz",
        }

        result = get_system_prompt(state)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_includes_credentials(self):
        """Test that prompt includes user credentials."""
        state = {
            "email": "user@test.com",
            "secret": "my-secret-key",
            "current_url": "http://quiz.example.com",
        }

        result = get_system_prompt(state)

        assert "user@test.com" in result
        assert "my-secret-key" in result
        assert "http://quiz.example.com" in result

    def test_includes_tool_descriptions(self):
        """Test that prompt includes tool descriptions."""
        state = {
            "email": "test@example.com",
            "secret": "secret",
            "current_url": "http://example.com",
        }

        result = get_system_prompt(state)

        assert "python_tool" in result
        assert "javascript_tool" in result
        assert "download_file_tool" in result
        assert "submit_answer_tool" in result
        assert "call_llm_tool" in result
        assert "call_llm_with_multiple_files_tool" in result

    def test_handles_missing_state_fields(self):
        """Test that prompt handles missing state fields gracefully."""
        state = {}

        result = get_system_prompt(state)

        assert "UNKNOWN" in result

    def test_includes_temp_directory(self, mocker):
        """Test that prompt includes the temp directory path."""
        mocker.patch("app.nodes.agent.settings.TEMP_DIR", "/custom/temp/dir")

        state = {
            "email": "test@example.com",
            "secret": "secret",
            "current_url": "http://example.com",
        }

        result = get_system_prompt(state)

        assert "/custom/temp/dir" in result or "temp" in result.lower()


class TestAgentNode:
    """Test cases for agent_node function."""

    @pytest.mark.asyncio
    async def test_agent_node_returns_messages(self, mocker):
        """Test that agent_node returns messages."""
        mock_llm_client = AsyncMock()
        mock_response = AIMessage(content="I will analyze this.")
        mock_llm_client.chat.return_value = mock_response

        mock_resources = MagicMock()
        mock_resources.llm_client = mock_llm_client

        state = {
            "email": "test@example.com",
            "secret": "secret",
            "current_url": "http://example.com",
            "messages": [],
            "resources": mock_resources,
            "tools": [],
        }

        result = await agent_node(state)

        assert "messages" in result
        assert len(result["messages"]) == 1
        assert result["messages"][0] == mock_response

    @pytest.mark.asyncio
    async def test_agent_node_includes_system_message(self, mocker):
        """Test that agent_node prepends system message to messages."""
        mock_llm_client = AsyncMock()
        mock_response = AIMessage(content="Response")
        mock_llm_client.chat.return_value = mock_response

        mock_resources = MagicMock()
        mock_resources.llm_client = mock_llm_client

        state = {
            "email": "test@example.com",
            "secret": "secret",
            "current_url": "http://example.com",
            "messages": [],
            "resources": mock_resources,
            "tools": [],
        }

        await agent_node(state)

        # Check that chat was called with messages starting with SystemMessage
        call_args = mock_llm_client.chat.call_args
        messages = call_args.kwargs.get(
            "messages", call_args.args[0] if call_args.args else []
        )

        assert len(messages) > 0
        assert isinstance(messages[0], SystemMessage)

    @pytest.mark.asyncio
    async def test_agent_node_passes_tools(self, mocker):
        """Test that agent_node passes tools to LLM."""
        mock_llm_client = AsyncMock()
        mock_response = AIMessage(content="Response")
        mock_llm_client.chat.return_value = mock_response

        mock_resources = MagicMock()
        mock_resources.llm_client = mock_llm_client

        mock_tool = MagicMock()
        mock_tool.name = "test_tool"

        state = {
            "email": "test@example.com",
            "secret": "secret",
            "current_url": "http://example.com",
            "messages": [],
            "resources": mock_resources,
            "tools": [mock_tool],
        }

        await agent_node(state)

        call_args = mock_llm_client.chat.call_args
        assert call_args.kwargs.get("tools") == [mock_tool]

    @pytest.mark.asyncio
    async def test_agent_node_preserves_existing_messages(self, mocker):
        """Test that agent_node preserves existing messages."""
        mock_llm_client = AsyncMock()
        mock_response = AIMessage(content="New response")
        mock_llm_client.chat.return_value = mock_response

        mock_resources = MagicMock()
        mock_resources.llm_client = mock_llm_client

        existing_message = AIMessage(content="Previous message")

        state = {
            "email": "test@example.com",
            "secret": "secret",
            "current_url": "http://example.com",
            "messages": [existing_message],
            "resources": mock_resources,
            "tools": [],
        }

        await agent_node(state)

        # The chat should receive the existing messages (after system message)
        call_args = mock_llm_client.chat.call_args
        messages = call_args.kwargs.get(
            "messages", call_args.args[0] if call_args.args else []
        )

        # Should have system message + existing message
        assert len(messages) == 2
