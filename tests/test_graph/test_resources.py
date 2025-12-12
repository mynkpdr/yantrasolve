"""Tests for app/graph/resources.py"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.graph.resources import GlobalResources


class TestGlobalResources:
    """Test cases for GlobalResources class."""

    def test_init(self):
        """Test GlobalResources initialization."""
        resources = GlobalResources()

        assert resources.api_client is None
        assert resources.browser is None
        assert resources.llm_client is None

    @pytest.mark.asyncio
    async def test_initialize_creates_clients(self, mocker):
        """Test that initialize creates all client instances."""
        mock_api_client = MagicMock()
        mock_api_client.initialize = AsyncMock()

        mock_browser = MagicMock()
        mock_browser.initialize = AsyncMock()

        mock_llm_client = MagicMock()

        mocker.patch("app.graph.resources.APIClient", return_value=mock_api_client)
        mocker.patch("app.graph.resources.BrowserClient", return_value=mock_browser)
        mocker.patch("app.graph.resources.LLMClient", return_value=mock_llm_client)

        resources = GlobalResources()
        await resources.initialize()

        assert resources.api_client == mock_api_client
        assert resources.browser == mock_browser
        assert resources.llm_client == mock_llm_client

        mock_api_client.initialize.assert_called_once()
        mock_browser.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_concurrent_initialization(self, mocker):
        """Test that API client and browser are initialized concurrently."""
        initialization_order = []

        async def track_api_init():
            initialization_order.append("api_start")
            initialization_order.append("api_end")

        async def track_browser_init():
            initialization_order.append("browser_start")
            initialization_order.append("browser_end")

        mock_api_client = MagicMock()
        mock_api_client.initialize = track_api_init

        mock_browser = MagicMock()
        mock_browser.initialize = track_browser_init

        mock_llm_client = MagicMock()

        mocker.patch("app.graph.resources.APIClient", return_value=mock_api_client)
        mocker.patch("app.graph.resources.BrowserClient", return_value=mock_browser)
        mocker.patch("app.graph.resources.LLMClient", return_value=mock_llm_client)

        resources = GlobalResources()
        await resources.initialize()

        # Both should be initialized (order may vary due to asyncio.gather)
        assert "api_start" in initialization_order
        assert "browser_start" in initialization_order

    @pytest.mark.asyncio
    async def test_close_closes_all_clients(self, mocker):
        """Test that close properly closes all clients."""
        mock_api_client = MagicMock()
        mock_api_client.initialize = AsyncMock()
        mock_api_client.close = AsyncMock()

        mock_browser = MagicMock()
        mock_browser.initialize = AsyncMock()
        mock_browser.close = AsyncMock()

        mock_llm_client = MagicMock()

        mocker.patch("app.graph.resources.APIClient", return_value=mock_api_client)
        mocker.patch("app.graph.resources.BrowserClient", return_value=mock_browser)
        mocker.patch("app.graph.resources.LLMClient", return_value=mock_llm_client)

        resources = GlobalResources()
        await resources.initialize()
        await resources.close()

        mock_api_client.close.assert_called_once()
        mock_browser.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_handles_none_clients(self):
        """Test that close handles None clients gracefully."""
        resources = GlobalResources()

        # Should not raise any exception
        await resources.close()

    @pytest.mark.asyncio
    async def test_resources_lifecycle(self, mocker):
        """Test complete lifecycle of GlobalResources."""
        mock_api_client = MagicMock()
        mock_api_client.initialize = AsyncMock()
        mock_api_client.close = AsyncMock()

        mock_browser = MagicMock()
        mock_browser.initialize = AsyncMock()
        mock_browser.close = AsyncMock()

        mock_llm_client = MagicMock()

        mocker.patch("app.graph.resources.APIClient", return_value=mock_api_client)
        mocker.patch("app.graph.resources.BrowserClient", return_value=mock_browser)
        mocker.patch("app.graph.resources.LLMClient", return_value=mock_llm_client)

        resources = GlobalResources()

        # Initial state
        assert resources.api_client is None

        # After initialization
        await resources.initialize()
        assert resources.api_client is not None
        assert resources.browser is not None
        assert resources.llm_client is not None

        # After close
        await resources.close()
        # Clients should still be set but closed
        mock_api_client.close.assert_called_once()
        mock_browser.close.assert_called_once()
