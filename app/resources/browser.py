"""Browser automation client using Playwright."""

import asyncio
import hashlib
import json
from typing import Optional
from playwright.async_api import async_playwright, Browser, Playwright, Page
from app.config.settings import settings
from app.utils.cache import get_cache_key, cache_get, cache_set
from app.utils.logging import logger


class BrowserClient:
    """Headless browser for JS-rendered pages, screenshots, and console capture."""

    def __init__(self):
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self._initialized = False

    async def initialize(self):
        """Launch headless Chromium browser."""
        if self._initialized:
            return
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True, args=["--disable-blink-features=AutomationControlled"]
            )
            self._initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            raise

    async def fetch_page_content(self, url: str) -> dict:
        """Fetch page HTML, text, screenshot, and console logs.

        Args:
            url: URL of the page to fetch.

        Returns:
            Dict with 'html', 'text', 'screenshot_path', and 'console_logs'.
        """
        # Check cache
        cache_key = get_cache_key("fetch_page_content", url)
        hit, cached = cache_get(cache_key, ttl_seconds=3600)
        if hit:
            logger.info(f"Cache hit for page: {url}")
            return cached

        page: Optional[Page] = None
        try:
            page = await self.browser.new_page()
            console_logs = []

            async def handle_console(msg):
                for arg in msg.args:
                    try:
                        console_logs.append(
                            f"[{msg.type}] {json.dumps(await arg.json_value(), indent=2)}"
                        )
                    except Exception:
                        console_logs.append(f"[{msg.type}] {msg.text}")

            page.on("console", handle_console)
            page.set_default_timeout(settings.BROWSER_PAGE_TIMEOUT)
            await page.goto(url, wait_until="networkidle")
            await asyncio.sleep(1)

            raw_html = await page.content()
            full_text = await page.inner_text("body")
            filename = f"{hashlib.sha256(url.encode()).hexdigest()}.png"
            await page.screenshot(full_page=True, path=settings.TEMP_DIR / filename)

            data = {
                "html": raw_html,
                "text": full_text,
                "screenshot_path": str(settings.TEMP_DIR / filename),
                "console_logs": console_logs,
            }
            logger.info(f"Fetched page: {url} (length: {len(raw_html)})")
            cache_set(cache_key, data)
            return data

        except Exception as e:
            logger.error(f"Error fetching page {url}: {e}")
            raise
        finally:
            if page:
                await page.close()

    async def close(self) -> None:
        """Clean up browser resources."""
        if self.browser:
            logger.info("Closing browser")
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
        self._initialized = False

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
