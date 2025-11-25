import asyncio

from app.resources.api import APIClient
from app.resources.browser import BrowserClient
from app.resources.llm import LLMClient

from app.utils.logging import logger


class GlobalResources:
    """A container for shared, long-lived resources."""

    def __init__(self):
        self.api_client: APIClient | None = None
        self.browser: BrowserClient | None = None
        self.llm_client: LLMClient | None = None

    async def initialize(self) -> None:
        """Initialize all resources concurrently."""
        self.api_client = APIClient()
        self.browser = BrowserClient()
        self.llm_client = LLMClient()
        logger.info("Initializing global resources...")

        # Use asyncio.gather for concurrent initialization
        await asyncio.gather(
            self.api_client.initialize(),
            self.browser.initialize(),
        )
        logger.info("Global resources initialized.")

    async def close(self) -> None:
        """Close all resources concurrently."""
        if self.api_client:
            await asyncio.gather(
                self.api_client.close(),
                self.browser.close(),
            )
        logger.info("Global resources closed.")
