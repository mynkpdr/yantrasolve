import pytest
from unittest.mock import AsyncMock, MagicMock

from app.resources.browser import BrowserClient


class TestBrowserClient:
    @pytest.mark.asyncio
    async def test_init(self):
        """Test initialization of BrowserClient."""
        client = BrowserClient()
        assert client.playwright is None
        assert client.browser is None
        assert client._initialized is False

    @pytest.mark.asyncio
    async def test_initialize_success(self, mocker):
        """Test successful browser initialization."""
        client = BrowserClient()

        # Mock playwright
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_playwright.chromium.launch.return_value = mock_browser

        mock_async_playwright_instance = MagicMock()
        mock_start = AsyncMock(return_value=mock_playwright)
        mock_async_playwright_instance.start = mock_start

        mock_async_playwright = MagicMock(return_value=mock_async_playwright_instance)

        mocker.patch("app.resources.browser.async_playwright", mock_async_playwright)

        await client.initialize()

        assert client.playwright == mock_playwright
        assert client.browser == mock_browser
        assert client._initialized is True

        mock_async_playwright.assert_called_once()
        mock_start.assert_called_once()
        mock_playwright.chromium.launch.assert_called_once_with(
            headless=True, args=["--disable-blink-features=AutomationControlled"]
        )

    @pytest.mark.asyncio
    async def test_initialize_already_initialized(self, mocker):
        """Test that initialize does nothing if already initialized."""
        client = BrowserClient()
        client._initialized = True

        mock_async_playwright = MagicMock()
        mocker.patch("app.resources.browser.async_playwright", mock_async_playwright)

        await client.initialize()

        # Should not call anything
        mock_async_playwright.assert_not_called()

    @pytest.mark.asyncio
    async def test_initialize_error(self, mocker):
        """Test initialization failure."""
        client = BrowserClient()

        mock_async_playwright_instance = MagicMock()
        mock_start = AsyncMock(side_effect=Exception("Playwright error"))
        mock_async_playwright_instance.start = mock_start

        mock_async_playwright = MagicMock(return_value=mock_async_playwright_instance)

        mocker.patch("app.resources.browser.async_playwright", mock_async_playwright)

        with pytest.raises(Exception, match="Playwright error"):
            await client.initialize()

        assert client._initialized is False

    @pytest.mark.asyncio
    async def test_close(self, mocker):
        """Test closing the browser."""
        client = BrowserClient()
        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()

        client.playwright = mock_playwright
        client.browser = mock_browser
        client._initialized = True

        await client.close()

        mock_browser.close.assert_called_once()
        mock_playwright.stop.assert_called_once()
        assert client.browser is None
        assert client.playwright is None
        assert client._initialized is False

    @pytest.mark.asyncio
    async def test_close_no_browser(self, mocker):
        """Test closing when browser is not initialized."""
        client = BrowserClient()

        # No mocks needed since nothing is set
        await client.close()

        assert client.browser is None
        assert client.playwright is None
        assert client._initialized is False

    @pytest.mark.asyncio
    async def test_context_manager(self, mocker):
        """Test async context manager."""
        client = BrowserClient()

        mock_playwright = AsyncMock()
        mock_browser = AsyncMock()
        mock_playwright.chromium.launch.return_value = mock_browser

        mock_async_playwright_instance = MagicMock()
        mock_start = AsyncMock(return_value=mock_playwright)
        mock_async_playwright_instance.start = mock_start

        mock_async_playwright = MagicMock(return_value=mock_async_playwright_instance)

        mocker.patch("app.resources.browser.async_playwright", mock_async_playwright)

        async with client as ctx_client:
            assert ctx_client == client
            assert client._initialized is True

        assert client._initialized is False
        mock_browser.close.assert_called_once()
        mock_playwright.stop.assert_called_once()
