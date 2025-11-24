import asyncio

from app.resources.api import APIClient

from app.utils.logging import logger


class GlobalResources:
    """A container for shared, long-lived resources."""

    def __init__(self):
        self.api_client: APIClient | None = None

    async def initialize(self) -> None:
        """Initialize all resources concurrently."""
        self.api_client = APIClient()

        # Use asyncio.gather for concurrent initialization
        await asyncio.gather(self.api_client.initialize())
        logger.info("Global resources initialized.")

    async def close(self) -> None:
        """Close all resources concurrently."""
        if self.api_client:
            await asyncio.gather(self.api_client.close())
        logger.info("Global resources closed.")
