from typing import Optional, Dict, Any
import httpx

from app.utils.helpers import retry_with_backoff
from app.utils.logging import logger


class APIClient:
    """Async HTTP client for APIs."""

    def __init__(self, timeout: int = 30):
        self.client: Optional[httpx.AsyncClient] = None
        self.timeout = timeout

    async def initialize(self):
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
        """Call an API"""
        method = method.upper()
        headers = headers or {}
        headers.setdefault("User-Agent", "YantraSolve/1.0")

        async def request():
            resp = await self.client.request(
                method=method, url=url, headers=headers, params=params, json=json_data
            )
            resp.raise_for_status()
            content_type = resp.headers.get("Content-Type", "")
            return (
                resp.json()
                if "application/json" in content_type
                else {"content": resp.text}
            )

        try:
            result = await retry_with_backoff(request, max_retries=3)
            return result
        except httpx.HTTPStatusError as e:
            logger.error(f"API error {e.response.status_code}: {url}")
            return {"error": str(e), "status": e.response.status_code}
        except Exception as e:
            logger.error(f"API call failed: {url} - {e}")
            return {"error": str(e), "status": None}

    async def close(self):
        if self.client:
            await self.client.aclose()
            self.client = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
