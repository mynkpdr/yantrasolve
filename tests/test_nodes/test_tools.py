"""Tests for app/nodes/tools.py"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.messages import ToolMessage

from app.nodes.tools import tool_execution_node


class TestToolExecutionNode:
    """Test cases for tool_execution_node function."""

    @pytest.fixture
    def mock_python_tool(self):
        """Create a mock Python tool."""
        tool = AsyncMock()
        tool.name = "python_tool"
        tool.ainvoke.return_value = "Result: 42"
        return tool

    @pytest.fixture
    def mock_download_tool(self):
        """Create a mock download tool."""
        tool = AsyncMock()
        tool.name = "download_file_tool"
        tool.ainvoke.return_value = "/tmp/file.csv"
        return tool

    @pytest.mark.asyncio
    async def test_executes_single_tool(self, mock_python_tool):
        """Test executing a single tool call."""
        mock_message = MagicMock()
        mock_message.tool_calls = [
            {"name": "python_tool", "id": "call-1", "args": {"code": "print(42)"}}
        ]

        state = {
            "messages": [mock_message],
            "tools": [mock_python_tool],
        }

        result = await tool_execution_node(state)

        mock_python_tool.ainvoke.assert_called_once_with({"code": "print(42)"})
        assert len(result["messages"]) == 1
        assert isinstance(result["messages"][0], ToolMessage)

    @pytest.mark.asyncio
    async def test_executes_multiple_tools(self, mock_python_tool, mock_download_tool):
        """Test executing multiple tool calls."""
        mock_message = MagicMock()
        mock_message.tool_calls = [
            {"name": "python_tool", "id": "call-1", "args": {"code": "print(1)"}},
            {
                "name": "download_file_tool",
                "id": "call-2",
                "args": {"url": "http://example.com/file.csv"},
            },
        ]

        state = {
            "messages": [mock_message],
            "tools": [mock_python_tool, mock_download_tool],
        }

        result = await tool_execution_node(state)

        assert len(result["messages"]) == 2
        mock_python_tool.ainvoke.assert_called_once()
        mock_download_tool.ainvoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_no_tool_calls(self):
        """Test handling when no tool calls are present."""
        mock_message = MagicMock()
        mock_message.tool_calls = None

        state = {
            "messages": [mock_message],
            "tools": [],
        }

        result = await tool_execution_node(state)

        assert result["messages"] == []

    @pytest.mark.asyncio
    async def test_handles_empty_tool_calls(self):
        """Test handling when tool_calls is empty list."""
        mock_message = MagicMock()
        mock_message.tool_calls = []

        state = {
            "messages": [mock_message],
            "tools": [],
        }

        result = await tool_execution_node(state)

        assert result["messages"] == []

    @pytest.mark.asyncio
    async def test_handles_tool_not_found(self):
        """Test handling when tool is not found."""
        mock_message = MagicMock()
        mock_message.tool_calls = [
            {"name": "nonexistent_tool", "id": "call-1", "args": {}}
        ]

        state = {
            "messages": [mock_message],
            "tools": [],
        }

        result = await tool_execution_node(state)

        assert len(result["messages"]) == 1
        assert "not found" in result["messages"][0].content

    @pytest.mark.asyncio
    async def test_handles_tool_execution_error(self, mock_python_tool):
        """Test handling when tool execution raises an error."""
        mock_python_tool.ainvoke.side_effect = Exception("Execution failed")

        mock_message = MagicMock()
        mock_message.tool_calls = [
            {"name": "python_tool", "id": "call-1", "args": {"code": "invalid"}}
        ]

        state = {
            "messages": [mock_message],
            "tools": [mock_python_tool],
        }

        result = await tool_execution_node(state)

        assert len(result["messages"]) == 1
        assert "Error" in result["messages"][0].content

    @pytest.mark.asyncio
    async def test_tool_message_has_correct_tool_call_id(mock_python_tool):
        mock_message = MagicMock()
        mock_message.tool_calls = [
            {"name": "python_tool", "id": "unique-id-123", "args": {}}
        ]

        mock_python_tool.run = AsyncMock(return_value={"output": "dummy"})

        state = {
            "messages": [mock_message],
            "tools": [mock_python_tool],
        }

        result = await tool_execution_node(state)

        assert result["messages"][0].tool_call_id == "unique-id-123"

    @pytest.mark.asyncio
    async def test_tool_message_contains_result(self, mock_python_tool):
        """Test that ToolMessage contains the tool result."""
        mock_python_tool.ainvoke.return_value = "Calculated value: 100"

        mock_message = MagicMock()
        mock_message.tool_calls = [{"name": "python_tool", "id": "call-1", "args": {}}]

        state = {
            "messages": [mock_message],
            "tools": [mock_python_tool],
        }

        result = await tool_execution_node(state)

        assert "Calculated value: 100" in result["messages"][0].content

    @pytest.mark.asyncio
    async def test_partial_success_on_multiple_tools(
        self, mock_python_tool, mock_download_tool
    ):
        """Test that partial success is handled when one tool fails."""
        mock_download_tool.ainvoke.side_effect = Exception("Download failed")

        mock_message = MagicMock()
        mock_message.tool_calls = [
            {"name": "python_tool", "id": "call-1", "args": {}},
            {"name": "download_file_tool", "id": "call-2", "args": {}},
        ]

        state = {
            "messages": [mock_message],
            "tools": [mock_python_tool, mock_download_tool],
        }

        result = await tool_execution_node(state)

        # Both should have messages, one success and one error
        assert len(result["messages"]) == 2
        assert "Result: 42" in result["messages"][0].content
        assert "Error" in result["messages"][1].content
