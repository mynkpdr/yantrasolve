import asyncio
import hashlib
import json
from typing import Optional
from playwright.async_api import async_playwright, Browser, Playwright, Page

from app.config.settings import settings
from app.utils.cache import get_cache_key, cache_get, cache_set
from app.utils.logging import logger


class BrowserClient:
    """
    Browser automation tool using Playwright.

    Handles JavaScript-rendered pages, dynamic content, and screenshot capture
    for vision analysis.
    """

    def __init__(self):
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self._initialized = False

    async def initialize(self):
        if self._initialized:
            return

        try:
            self.playwright = await async_playwright().start()

            # Launch browser
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled"
                ],  # Avoid detection
            )

            self._initialized = True

        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            raise

    async def fetch_page_content(self, url: str) -> dict:
        """
        Fetches the content of a web page, including rendered HTML, visible text,

        Args:
            url (str): The URL of the page to fetch.

        Returns:
            dict: A dictionary containing 'html', 'text', 'screenshot_path', and 'console_logs'.
        """
        # Check cache first
        cache_key = get_cache_key("fetch_page_content", url)
        hit, cached_data = cache_get(cache_key, ttl_seconds=3600)
        if hit:
            logger.info(f"Cache hit for page: {url}")
            return cached_data

        page: Optional[Page] = None
        try:
            logger.info(f"Fetching page: {url}")

            # Create new page
            page = await self.browser.new_page()

            # Intercept console messages
            console_logs = []

            async def handle_console(msg):
                for arg in msg.args:
                    try:
                        # Convert argument to JSON in the browser
                        json_value = await arg.json_value()
                        console_logs.append(
                            f"[{msg.type}] {json.dumps(json_value, indent=2)}"
                        )
                    except Exception:
                        console_logs.append(f"[{msg.type}] {msg.text}")

            page.on("console", handle_console)

            # Set timeout
            page.set_default_timeout(settings.BROWSER_PAGE_TIMEOUT)

            # Navigate to URL
            await page.goto(url, wait_until="networkidle")

            # Wait a bit for JavaScript to execute
            await asyncio.sleep(1)

            # Get rendered HTML
            raw_html = await page.content()

            # Get visible text
            full_text = await page.inner_text("body")

            # Capture screenshot
            filename = f"{hashlib.sha256(url.encode('utf-8')).hexdigest()}.png"
            await page.screenshot(full_page=True, path=settings.TEMP_DIR / filename)

            data = {
                "html": raw_html,
                "text": full_text,
                "screenshot_path": str(settings.TEMP_DIR / filename),
                "console_logs": console_logs,
            }
            logger.info(f"Successfully fetched page: {url} (length: {len(raw_html)})")

            # Cache the result
            cache_set(cache_key, data)

            return data

        except Exception as e:
            logger.error(f"Error fetching page {url}: {e}")
            raise
        finally:
            if page:
                await page.close()

    async def close(self) -> None:
        """Cleanup browser resources."""
        if self.browser:
            logger.info("Closing browser")
            await self.browser.close()
            self.browser = None

        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

        self._initialized = False

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
