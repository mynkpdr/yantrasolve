from langchain_core.tools import tool
from app.resources.browser import BrowserClient
from app.utils.logging import logger
import asyncio
import json


def create_javascript_tool(browser_client: BrowserClient):
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

            # Create a new page and navigate to the URL
            page = await browser_client.browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=30000)

            # Wait a bit for JavaScript to execute
            await asyncio.sleep(1)

            # Evaluate the JavaScript code
            result = await page.evaluate(code)

            # Convert result to string if needed
            if result is None:
                return "JavaScript executed successfully. (No value returned)"
            elif isinstance(result, (dict, list)):
                return json.dumps(result, indent=2, ensure_ascii=False)
            else:
                return str(result)

        except Exception as e:
            error_msg = str(e)
            logger.error(f"JavaScript execution error: {error_msg}")

            # Provide helpful hints for common errors
            if "Timeout" in error_msg:
                error_msg += "\nHint: Page took too long to load. Try a simpler selector or check if the URL is correct."
            elif "Cannot read properties" in error_msg or "undefined" in error_msg:
                error_msg += "\nHint: The element or property may not exist. Check if the selector is correct."

            return f"JavaScript Error: {error_msg}"
        finally:
            if page:
                await page.close()

    return javascript_tool
