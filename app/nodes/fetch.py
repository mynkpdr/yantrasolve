"""Fetch node for retrieving page content."""

from app.graph.state import QuizState
from app.utils.logging import logger
from langchain_core.messages import HumanMessage


async def fetch_context_node(state: QuizState) -> dict:
    """Fetch page content, screenshot, and console logs from URL."""
    logger.info(f"Fetching context for {state['current_url']}")
    try:
        browser = state["resources"].browser
        data = await browser.fetch_page_content(state["current_url"])

        # Truncate HTML and logs to avoid hitting token limits
        html = data["html"][:20000] + ("..." if len(data["html"]) > 20000 else "")
        logs = (
            "\n".join(data["console_logs"][:10000])
            if data["console_logs"]
            else "No console logs."
        )

        return {
            "messages": [
                HumanMessage(
                    content=[
                        {
                            "type": "text",
                            "text": f"""I have visited the URL: {state['current_url']}

The page contains the following HTML content:

{"#" * 15 + " HTML Content Start " + "#" * 15}
{html}
{"#" * 15 + " HTML Content End " + "#" * 15}

The console logs during page (Don't ignore them, sometimes they contain important info):

{"#" * 15 + " Console Logs Start " + "#" * 15}
{logs}
{"#" * 15 + " Console Logs End " + "#" * 15}

The screenshot of the page has been saved at: {data['screenshot_path']}
Use the screenshot path if you need to reference visual elements on the page.

Please analyze this information and submit the answer.""",
                        }
                    ]
                )
            ],
            "html": data["html"],
            "text": data["text"],
            "console_logs": data["console_logs"],
            "screenshot_path": data["screenshot_path"],
        }
    except Exception as e:
        logger.error(f"Error fetching page: {e}")
        return {"messages": [HumanMessage(content=f"Error fetching page: {e}")]}
