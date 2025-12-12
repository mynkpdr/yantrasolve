"""Tests for app/nodes/fetch.py"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from langchain_core.messages import HumanMessage

from app.nodes.fetch import fetch_context_node


class TestFetchContextNode:
    """Test cases for fetch_context_node function."""

    @pytest.fixture
    def mock_browser_data(self):
        """Create mock browser data."""
        return {
            "html": "<html><body><h1>Quiz Question</h1></body></html>",
            "text": "Quiz Question",
            "console_logs": ["[log] Loaded quiz"],
            "screenshot_path": "/tmp/screenshot.png",
        }

    @pytest.mark.asyncio
    async def test_fetch_context_returns_page_data(self, mock_browser_data):
        """Test that fetch_context_node returns page data."""
        mock_browser = AsyncMock()
        mock_browser.fetch_page_content.return_value = mock_browser_data

        mock_resources = MagicMock()
        mock_resources.browser = mock_browser

        state = {
            "current_url": "http://example.com/quiz",
            "resources": mock_resources,
        }

        result = await fetch_context_node(state)

        assert result["html"] == mock_browser_data["html"]
        assert result["text"] == mock_browser_data["text"]
        assert result["console_logs"] == mock_browser_data["console_logs"]
        assert result["screenshot_path"] == mock_browser_data["screenshot_path"]

    @pytest.mark.asyncio
    async def test_fetch_context_returns_human_message(self, mock_browser_data):
        """Test that fetch_context_node returns a HumanMessage."""
        mock_browser = AsyncMock()
        mock_browser.fetch_page_content.return_value = mock_browser_data

        mock_resources = MagicMock()
        mock_resources.browser = mock_browser

        state = {
            "current_url": "http://example.com/quiz",
            "resources": mock_resources,
        }

        result = await fetch_context_node(state)

        assert "messages" in result
        assert len(result["messages"]) == 1
        assert isinstance(result["messages"][0], HumanMessage)

    @pytest.mark.asyncio
    async def test_fetch_context_message_contains_url(self, mock_browser_data):
        """Test that the message contains the URL."""
        mock_browser = AsyncMock()
        mock_browser.fetch_page_content.return_value = mock_browser_data

        mock_resources = MagicMock()
        mock_resources.browser = mock_browser

        state = {
            "current_url": "http://example.com/quiz",
            "resources": mock_resources,
        }

        result = await fetch_context_node(state)

        message = result["messages"][0]
        # Content is a list with a text dict
        content = (
            message.content[0]["text"]
            if isinstance(message.content, list)
            else message.content
        )

        assert "http://example.com/quiz" in content

    @pytest.mark.asyncio
    async def test_fetch_context_message_contains_html(self, mock_browser_data):
        """Test that the message contains HTML content."""
        mock_browser = AsyncMock()
        mock_browser.fetch_page_content.return_value = mock_browser_data

        mock_resources = MagicMock()
        mock_resources.browser = mock_browser

        state = {
            "current_url": "http://example.com/quiz",
            "resources": mock_resources,
        }

        result = await fetch_context_node(state)

        message = result["messages"][0]
        content = (
            message.content[0]["text"]
            if isinstance(message.content, list)
            else message.content
        )

        assert "Quiz Question" in content

    @pytest.mark.asyncio
    async def test_fetch_context_truncates_long_html(self):
        """Test that long HTML content is truncated."""
        long_html = "x" * 40000
        mock_browser_data = {
            "html": long_html,
            "text": "Text",
            "console_logs": [],
            "screenshot_path": "/tmp/screenshot.png",
        }

        mock_browser = AsyncMock()
        mock_browser.fetch_page_content.return_value = mock_browser_data

        mock_resources = MagicMock()
        mock_resources.browser = mock_browser

        state = {
            "current_url": "http://example.com/quiz",
            "resources": mock_resources,
        }

        result = await fetch_context_node(state)

        message = result["messages"][0]
        content = (
            message.content[0]["text"]
            if isinstance(message.content, list)
            else message.content
        )

        # Content should be truncated (check for "...")
        assert "..." in content

    @pytest.mark.asyncio
    async def test_fetch_context_handles_empty_console_logs(self):
        """Test handling of empty console logs."""
        mock_browser_data = {
            "html": "<html></html>",
            "text": "",
            "console_logs": [],
            "screenshot_path": "/tmp/screenshot.png",
        }

        mock_browser = AsyncMock()
        mock_browser.fetch_page_content.return_value = mock_browser_data

        mock_resources = MagicMock()
        mock_resources.browser = mock_browser

        state = {
            "current_url": "http://example.com/quiz",
            "resources": mock_resources,
        }

        result = await fetch_context_node(state)

        message = result["messages"][0]
        content = (
            message.content[0]["text"]
            if isinstance(message.content, list)
            else message.content
        )

        assert "No console logs" in content

    @pytest.mark.asyncio
    async def test_fetch_context_handles_browser_error(self):
        """Test handling of browser errors."""
        mock_browser = AsyncMock()
        mock_browser.fetch_page_content.side_effect = Exception("Browser error")

        mock_resources = MagicMock()
        mock_resources.browser = mock_browser

        state = {
            "current_url": "http://example.com/quiz",
            "resources": mock_resources,
        }

        result = await fetch_context_node(state)

        assert "messages" in result
        message = result["messages"][0]
        content = (
            message.content
            if isinstance(message.content, str)
            else message.content[0]["text"]
        )

        assert "Error" in content or "error" in content.lower()

    @pytest.mark.asyncio
    async def test_fetch_context_calls_browser_with_url(self, mock_browser_data):
        """Test that browser is called with the correct URL."""
        mock_browser = AsyncMock()
        mock_browser.fetch_page_content.return_value = mock_browser_data

        mock_resources = MagicMock()
        mock_resources.browser = mock_browser

        state = {
            "current_url": "http://example.com/quiz/123",
            "resources": mock_resources,
        }

        await fetch_context_node(state)

        mock_browser.fetch_page_content.assert_called_once_with(
            "http://example.com/quiz/123"
        )
