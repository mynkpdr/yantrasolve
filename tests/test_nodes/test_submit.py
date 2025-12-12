"""Tests for app/nodes/submit.py"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from langchain_core.messages import ToolMessage

from app.nodes.submit import submit_node


class TestSubmitNode:
    """Test cases for submit_node function."""

    @pytest.fixture
    def mock_submit_tool(self):
        """Create a mock submit tool."""
        tool = AsyncMock()
        tool.name = "submit_answer_tool"
        tool.ainvoke.return_value = {
            "correct": True,
            "url": "http://example.com/next",
        }
        return tool

    @pytest.mark.asyncio
    async def test_submit_node_executes_tool(self, mock_submit_tool):
        """Test that submit_node executes the submit tool."""
        mock_message = MagicMock()
        mock_message.tool_calls = [
            {
                "name": "submit_answer_tool",
                "id": "call-123",
                "args": {
                    "post_endpoint_url": "http://api.example.com/submit",
                    "payload": {"answer": "42"},
                },
            }
        ]

        state = {
            "messages": [mock_message],
            "tools": [mock_submit_tool],
            "submitted_answers": [],
        }

        await submit_node(state)

        mock_submit_tool.ainvoke.assert_called_once_with(
            {
                "post_endpoint_url": "http://api.example.com/submit",
                "payload": {"answer": "42"},
            }
        )

    @pytest.mark.asyncio
    async def test_submit_node_returns_submission_result(self, mock_submit_tool):
        """Test that submit_node returns the submission result."""
        mock_message = MagicMock()
        mock_message.tool_calls = [
            {
                "name": "submit_answer_tool",
                "id": "call-123",
                "args": {"payload": {"answer": "42"}},
            }
        ]

        state = {
            "messages": [mock_message],
            "tools": [mock_submit_tool],
            "submitted_answers": [],
        }

        result = await submit_node(state)

        assert "submission_result" in result
        assert result["submission_result"]["correct"] is True

    @pytest.mark.asyncio
    async def test_submit_node_returns_tool_message(self, mock_submit_tool):
        """Test that submit_node returns a ToolMessage."""
        mock_message = MagicMock()
        mock_message.tool_calls = [
            {
                "name": "submit_answer_tool",
                "id": "call-123",
                "args": {"payload": {"answer": "42"}},
            }
        ]

        state = {
            "messages": [mock_message],
            "tools": [mock_submit_tool],
            "submitted_answers": [],
        }

        result = await submit_node(state)

        assert "messages" in result
        assert len(result["messages"]) == 1
        assert isinstance(result["messages"][0], ToolMessage)

    @pytest.mark.asyncio
    async def test_submit_node_stores_answer_payload(self, mock_submit_tool):
        """Test that submit_node stores the answer payload."""
        mock_message = MagicMock()
        mock_message.tool_calls = [
            {
                "name": "submit_answer_tool",
                "id": "call-123",
                "args": {"payload": {"answer": "42", "url": "http://example.com"}},
            }
        ]

        state = {
            "messages": [mock_message],
            "tools": [mock_submit_tool],
            "submitted_answers": [],
        }

        result = await submit_node(state)

        assert "answer_payload" in result
        assert result["answer_payload"]["answer"] == "42"

    @pytest.mark.asyncio
    async def test_submit_node_updates_submitted_answers(self, mock_submit_tool):
        """Test that submit_node updates submitted_answers history."""
        mock_message = MagicMock()
        mock_message.tool_calls = [
            {
                "name": "submit_answer_tool",
                "id": "call-123",
                "args": {"payload": {"answer": "42"}},
            }
        ]

        state = {
            "messages": [mock_message],
            "tools": [mock_submit_tool],
            "submitted_answers": [{"payload": {"answer": "41"}}],
        }

        result = await submit_node(state)

        assert "submitted_answers" in result
        assert len(result["submitted_answers"]) == 2

    @pytest.mark.asyncio
    async def test_submit_node_handles_last_tool_call(self, mock_submit_tool):
        """Test that submit_node uses the last tool call."""
        mock_other_tool = AsyncMock()
        mock_other_tool.name = "python_tool"

        mock_message = MagicMock()
        mock_message.tool_calls = [
            {"name": "python_tool", "id": "call-1", "args": {}},
            {
                "name": "submit_answer_tool",
                "id": "call-2",
                "args": {"payload": {"answer": "final"}},
            },
        ]

        state = {
            "messages": [mock_message],
            "tools": [mock_other_tool, mock_submit_tool],
            "submitted_answers": [],
        }

        result = await submit_node(state)

        # Should use the last tool call (submit_answer_tool)
        mock_submit_tool.ainvoke.assert_called_once()
        assert result["answer_payload"]["answer"] == "final"

    @pytest.mark.asyncio
    async def test_submit_node_tool_message_has_correct_id(self, mock_submit_tool):
        """Test that ToolMessage has the correct tool_call_id."""
        mock_message = MagicMock()
        mock_message.tool_calls = [
            {
                "name": "submit_answer_tool",
                "id": "unique-call-id",
                "args": {"payload": {}},
            }
        ]

        state = {
            "messages": [mock_message],
            "tools": [mock_submit_tool],
            "submitted_answers": [],
        }

        result = await submit_node(state)

        tool_message = result["messages"][0]
        assert tool_message.tool_call_id == "unique-call-id"
