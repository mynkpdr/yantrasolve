"""Tests for app/tools/javascript.py"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.tools.javascript import create_javascript_tool


class TestJavascriptTool:
    """Test cases for javascript_tool function."""

    @pytest.fixture
    def mock_browser_client(self):
        """Create a mock browser client."""
        browser_client = MagicMock()
        browser_client.browser = MagicMock()
        return browser_client

    @pytest.fixture
    def mock_page(self):
        """Create a mock page."""
        page = AsyncMock()
        page.goto = AsyncMock()
        page.evaluate = AsyncMock()
        page.close = AsyncMock()
        return page

    @pytest.mark.asyncio
    async def test_javascript_tool_creation(self, mock_browser_client):
        """Test that create_javascript_tool returns a tool."""
        tool = create_javascript_tool(mock_browser_client)

        assert tool is not None
        assert hasattr(tool, "ainvoke")
        assert tool.name == "javascript_tool"

    @pytest.mark.asyncio
    async def test_executes_javascript_code(self, mock_browser_client, mock_page):
        """Test executing JavaScript code."""
        mock_browser_client.browser.new_page = AsyncMock(return_value=mock_page)
        mock_page.evaluate.return_value = "Hello from JS"

        tool = create_javascript_tool(mock_browser_client)
        result = await tool.ainvoke(
            {
                "code": "return 'Hello from JS'",
                "url": "http://example.com",
            }
        )

        assert result == "Hello from JS"
        mock_page.goto.assert_called_once()
        mock_page.evaluate.assert_called_once_with("return 'Hello from JS'")

    @pytest.mark.asyncio
    async def test_returns_json_for_dict(self, mock_browser_client, mock_page):
        """Test that dict results are returned as JSON."""
        mock_browser_client.browser.new_page = AsyncMock(return_value=mock_page)
        mock_page.evaluate.return_value = {"key": "value", "count": 42}

        tool = create_javascript_tool(mock_browser_client)
        result = await tool.ainvoke(
            {
                "code": "return {key: 'value', count: 42}",
                "url": "http://example.com",
            }
        )

        assert '"key": "value"' in result
        assert '"count": 42' in result

    @pytest.mark.asyncio
    async def test_returns_json_for_list(self, mock_browser_client, mock_page):
        """Test that list results are returned as JSON."""
        mock_browser_client.browser.new_page = AsyncMock(return_value=mock_page)
        mock_page.evaluate.return_value = [1, 2, 3, 4, 5]

        tool = create_javascript_tool(mock_browser_client)
        result = await tool.ainvoke(
            {
                "code": "return [1, 2, 3, 4, 5]",
                "url": "http://example.com",
            }
        )

        assert "[1, 2, 3, 4, 5]" in result or "1" in result

    @pytest.mark.asyncio
    async def test_handles_none_result(self, mock_browser_client, mock_page):
        """Test handling of None/undefined result."""
        mock_browser_client.browser.new_page = AsyncMock(return_value=mock_page)
        mock_page.evaluate.return_value = None

        tool = create_javascript_tool(mock_browser_client)
        result = await tool.ainvoke(
            {
                "code": "console.log('test')",
                "url": "http://example.com",
            }
        )

        assert "successfully" in result.lower() or "No value" in result

    @pytest.mark.asyncio
    async def test_handles_timeout_error(self, mock_browser_client, mock_page):
        """Test handling of timeout error."""
        mock_browser_client.browser.new_page = AsyncMock(return_value=mock_page)
        mock_page.goto.side_effect = Exception("Timeout exceeded")

        tool = create_javascript_tool(mock_browser_client)
        result = await tool.ainvoke(
            {
                "code": "return 1",
                "url": "http://example.com",
            }
        )

        assert "Error" in result
        assert "Timeout" in result

    @pytest.mark.asyncio
    async def test_handles_undefined_error(self, mock_browser_client, mock_page):
        """Test handling of undefined property error."""
        mock_browser_client.browser.new_page = AsyncMock(return_value=mock_page)
        mock_page.evaluate.side_effect = Exception(
            "Cannot read properties of undefined"
        )

        tool = create_javascript_tool(mock_browser_client)
        result = await tool.ainvoke(
            {
                "code": "return undefined.property",
                "url": "http://example.com",
            }
        )

        assert "Error" in result
        assert "Hint" in result

    @pytest.mark.asyncio
    async def test_closes_page_on_success(self, mock_browser_client, mock_page):
        """Test that page is closed on success."""
        mock_browser_client.browser.new_page = AsyncMock(return_value=mock_page)
        mock_page.evaluate.return_value = "result"

        tool = create_javascript_tool(mock_browser_client)
        await tool.ainvoke(
            {
                "code": "return 'result'",
                "url": "http://example.com",
            }
        )

        mock_page.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_closes_page_on_error(self, mock_browser_client, mock_page):
        """Test that page is closed on error."""
        mock_browser_client.browser.new_page = AsyncMock(return_value=mock_page)
        mock_page.evaluate.side_effect = Exception("Error")

        tool = create_javascript_tool(mock_browser_client)
        await tool.ainvoke(
            {
                "code": "throw new Error()",
                "url": "http://example.com",
            }
        )

        mock_page.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_navigates_to_correct_url(self, mock_browser_client, mock_page):
        """Test that navigation goes to the correct URL."""
        mock_browser_client.browser.new_page = AsyncMock(return_value=mock_page)
        mock_page.evaluate.return_value = "ok"

        tool = create_javascript_tool(mock_browser_client)
        await tool.ainvoke(
            {
                "code": "return 'ok'",
                "url": "http://specific-url.com/page",
            }
        )

        mock_page.goto.assert_called_once()
        call_args = mock_page.goto.call_args
        assert call_args[0][0] == "http://specific-url.com/page"
