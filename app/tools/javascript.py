"""JavaScript execution tool for browser automation."""

import asyncio
import json
from langchain_core.tools import tool
from app.resources.browser import BrowserClient
from app.utils.logging import logger


def create_javascript_tool(browser_client: BrowserClient):
    """Factory to create a JavaScript tool bound to a browser client."""

    @tool
    async def javascript_tool(code: str, url: str) -> str:
        """
        Executes JavaScript code on the specified web page.
        Use this only when needed to interact with the page directly.

        Args:
            code: The JavaScript code to execute.
            url: The URL of the page to run the code on.

        Returns:
            The result of the JavaScript execution as a string.
        """
        page = None
        try:
            logger.info(f"Executing JavaScript on: {url}")
            page = await browser_client.browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(1)

            result = await page.evaluate(code)

            if result is None:
                return "JavaScript executed successfully. (No value returned)"
            elif isinstance(result, (dict, list)):
                return json.dumps(result, indent=2, ensure_ascii=False)
            return str(result)

        except Exception as e:
            error_msg = str(e)
            logger.error(f"JavaScript execution error: {error_msg}")
            if "Timeout" in error_msg:
                error_msg += (
                    "\nHint: Page took too long. Try simpler selector or check URL."
                )
            elif "Cannot read properties" in error_msg or "undefined" in error_msg:
                error_msg += "\nHint: Element/property may not exist. Check selector."
            return f"JavaScript Error: {error_msg}"
        finally:
            if page:
                await page.close()

    return javascript_tool
