"""Async HTTP client for API calls."""

from typing import Optional, Dict, Any
import httpx
from app.utils.helpers import retry_with_backoff
from app.utils.logging import logger


class APIClient:
    """Async HTTP client with retry support and context manager."""

    def __init__(self, timeout: int = 30):
        self.client: Optional[httpx.AsyncClient] = None
        self.timeout = timeout

    async def initialize(self):
        """Initialize the async HTTP client."""
        if self.client is None:
            self.client = httpx.AsyncClient(timeout=self.timeout)
        return self.client

    async def call_api(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an API request with retry logic."""
        headers = headers or {}
        headers.setdefault("User-Agent", "YantraSolve/1.0")

        async def request():
            resp = await self.client.request(
                method=method.upper(),
                url=url,
                headers=headers,
                params=params,
                json=json_data,
            )
            resp.raise_for_status()
            return (
                resp.json()
                if "application/json" in resp.headers.get("Content-Type", "")
                else {"content": resp.text}
            )

        try:
            return await retry_with_backoff(request, max_retries=3)
        except httpx.HTTPStatusError as e:
            logger.error(f"API error {e.response.status_code}: {url}")
            return {"error": str(e), "status": e.response.status_code}
        except Exception as e:
            logger.error(f"API call failed: {url} - {e}")
            return {"error": str(e), "status": None}

    async def close(self):
        """Close the HTTP client."""
        if self.client:
            await self.client.aclose()
            self.client = None

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
