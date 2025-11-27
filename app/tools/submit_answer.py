from typing import Dict, Any, Optional
from langchain_core.tools import tool
from app.utils.logging import logger
import httpx


@tool
async def submit_answer_tool(
    post_endpoint_url: str,
    payload: Dict[str, Any],
    headers: Optional[Dict[str, str]] = {},
) -> dict:
    """
    Submits the quiz answer payload to the specified URL via HTTP POST.

    Args:
        post_endpoint_url (str): The submission URL
        payload (Dict[str, Any]): The JSON payload containing the answer
        headers (Dict[str, str]): Headers to include in the request

    Returns:
        dict: Server response as JSON dictionary or error message
    """
    try:
        logger.info(
            f"Submitting answer to: {post_endpoint_url} with payload: {payload} and headers: {headers}"
        )

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                post_endpoint_url, json=payload, headers=headers
            )
            response.raise_for_status()
            result = response.json()
            return result

    except httpx.HTTPError as e:
        logger.error(f"Submission failed: {e}")
        return {"error": f"Submission failed: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"error": f"Unexpected error: {str(e)}"}
