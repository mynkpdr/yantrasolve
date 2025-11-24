import pytest
import httpx
from unittest.mock import AsyncMock, Mock

from app.resources.api import APIClient


class TestAPIClient:
    @pytest.mark.asyncio
    async def test_initialize(self, mocker):
        """Test client initialization."""
        client = APIClient()
        mock_httpx_client = AsyncMock()
        mocker.patch("httpx.AsyncClient", return_value=mock_httpx_client)

        result = await client.initialize()
        assert result == mock_httpx_client
        assert client.client == mock_httpx_client

    @pytest.mark.asyncio
    async def test_call_api_get_success_json(self, mocker):
        """Test successful GET request returning JSON."""
        client = APIClient()
        mock_response = Mock()
        mock_response.json.return_value = {"data": "test"}
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.raise_for_status.return_value = None

        mock_httpx_client = AsyncMock()
        mock_httpx_client.request.return_value = mock_response
        mocker.patch("httpx.AsyncClient", return_value=mock_httpx_client)

        await client.initialize()
        result = await client.call_api("http://example.com")

        assert result == {"data": "test"}
        mock_httpx_client.request.assert_called_once_with(
            method="GET",
            url="http://example.com",
            headers={"User-Agent": "YantraSolve/1.0"},
            params=None,
            json=None,
        )

    @pytest.mark.asyncio
    async def test_call_api_post_with_data(self, mocker):
        """Test POST request with JSON data."""
        client = APIClient()
        mock_response = Mock()
        mock_response.json.return_value = {"result": "ok"}
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.raise_for_status.return_value = None

        mock_httpx_client = AsyncMock()
        mock_httpx_client.request.return_value = mock_response
        mocker.patch("httpx.AsyncClient", return_value=mock_httpx_client)

        await client.initialize()
        result = await client.call_api(
            "http://example.com", method="POST", json_data={"key": "value"}
        )

        assert result == {"result": "ok"}
        mock_httpx_client.request.assert_called_once_with(
            method="POST",
            url="http://example.com",
            headers={"User-Agent": "YantraSolve/1.0"},
            params=None,
            json={"key": "value"},
        )

    @pytest.mark.asyncio
    async def test_call_api_with_custom_headers(self, mocker):
        """Test request with custom headers."""
        client = APIClient()
        mock_response = Mock()
        mock_response.json.return_value = {"data": "test"}
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.raise_for_status.return_value = None

        mock_httpx_client = AsyncMock()
        mock_httpx_client.request.return_value = mock_response
        mocker.patch("httpx.AsyncClient", return_value=mock_httpx_client)

        await client.initialize()
        await client.call_api(
            "http://example.com", headers={"Authorization": "Bearer mynky"}
        )

        expected_headers = {
            "User-Agent": "YantraSolve/1.0",
            "Authorization": "Bearer mynky",
        }
        mock_httpx_client.request.assert_called_once_with(
            method="GET",
            url="http://example.com",
            headers=expected_headers,
            params=None,
            json=None,
        )

    @pytest.mark.asyncio
    async def test_call_api_non_json_response(self, mocker):
        """Test response that is not JSON."""
        client = APIClient()
        mock_response = Mock()
        mock_response.text = "plain text"
        mock_response.headers = {"Content-Type": "text/plain"}
        mock_response.raise_for_status.return_value = None

        mock_httpx_client = AsyncMock()
        mock_httpx_client.request.return_value = mock_response
        mocker.patch("httpx.AsyncClient", return_value=mock_httpx_client)

        await client.initialize()
        result = await client.call_api("http://example.com")

        assert result == {"content": "plain text"}

    @pytest.mark.asyncio
    async def test_call_api_http_error(self, mocker):
        """Test HTTP status error."""
        client = APIClient()
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"

        http_error = httpx.HTTPStatusError(
            "404 Not Found", request=Mock(), response=mock_response
        )

        mock_httpx_client = AsyncMock()
        mock_httpx_client.request.side_effect = http_error
        mocker.patch("httpx.AsyncClient", return_value=mock_httpx_client)

        # Mock retry_with_backoff to just raise the error
        mock_retry = AsyncMock(side_effect=http_error)
        mocker.patch("app.resources.api.retry_with_backoff", mock_retry)

        await client.initialize()
        result = await client.call_api("http://example.com")

        assert result == {"error": str(http_error), "status": 404}

    @pytest.mark.asyncio
    async def test_call_api_general_error(self, mocker):
        """Test general exception."""
        client = APIClient()
        mock_httpx_client = AsyncMock()
        mock_httpx_client.request.side_effect = Exception("Network error")
        mocker.patch("httpx.AsyncClient", return_value=mock_httpx_client)

        mock_retry = AsyncMock(side_effect=Exception("Network error"))
        mocker.patch("app.resources.api.retry_with_backoff", mock_retry)

        await client.initialize()
        result = await client.call_api("http://example.com")

        assert result == {"error": "Network error", "status": None}

    @pytest.mark.asyncio
    async def test_close(self, mocker):
        """Test closing the client."""
        client = APIClient()
        mock_httpx_client = AsyncMock()
        mocker.patch("httpx.AsyncClient", return_value=mock_httpx_client)

        await client.initialize()
        await client.close()

        mock_httpx_client.aclose.assert_called_once()
        assert client.client is None

    @pytest.mark.asyncio
    async def test_context_manager(self, mocker):
        """Test async context manager."""
        mock_httpx_client = AsyncMock()
        mocker.patch("httpx.AsyncClient", return_value=mock_httpx_client)

        async with APIClient() as client:
            assert client.client == mock_httpx_client

        mock_httpx_client.aclose.assert_called_once()
