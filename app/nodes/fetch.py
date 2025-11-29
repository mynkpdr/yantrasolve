from app.utils.logging import logger
from app.graph.state import QuizState
from langchain_core.messages import HumanMessage


async def fetch_context_node(state: QuizState) -> dict:
    # Implementation of fetching context from the URL
    logger.info(f"\n{'#' * 30}\n1. Fetching context from URL...\n{'#' * 30}")
    try:
        browser_client = state["resources"].browser
        data = await browser_client.fetch_page_content(state["current_url"])

        resp = {
            "messages": [
                HumanMessage(
                    content=[
                        {
                            "type": "text",
                            "text": f"""I have visited the URL: {state['current_url']}

The page contains the following HTML content:

{"#" * 15 + " HTML Content Start " + "#" * 15}
{data['html'][:10000] + ("..." if len(data['html']) > 10000 else "")}
{"#" * 15 + " HTML Content End " + "#" * 15}


The console logs during page(Don't ignore them, sometimes they contain important info):

{"#" * 15 + " Console Logs Start " + "#" * 15}
{chr(10).join(data['console_logs'][:5000]) if data['console_logs'] else 'No console logs.'}
{"#" * 15 + " Console Logs End " + "#" * 15}


The screenshot of the page has been saved at: {data['screenshot_path']}
Use the screenshot path if you need to reference visual elements on the page.

Please analyze this information and submit the answer.""",
                        },
                    ]
                )
            ],
            "html": data["html"],
            "text": data["text"],
            "console_logs": data["console_logs"],
            "screenshot_path": data["screenshot_path"],
        }
        return resp
    except Exception as e:
        logger.error(f"Error fetching page: {e}")
        return {"messages": [HumanMessage(content=f"Error fetching page: {e}")]}
