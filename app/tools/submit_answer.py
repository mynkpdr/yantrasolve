from typing import Dict, Any
from langchain_core.tools import tool
from app.utils.logging import logger
import httpx


@tool
def submit_answer_tool(
    post_endpoint_url: str,
    payload: Dict[str, Any],
) -> dict:
    """
    Submits the quiz answer payload to the specified URL via HTTP POST.

    Args:
        post_endpoint_url: The submission URL (must start with http:// or https://)
        payload: The JSON payload containing email, secret, url, and answer

    Returns:
        Server response as JSON string or error message
    """
    try:
        headers = {"Content-Type": "application/json"}

        if not post_endpoint_url.startswith("http"):
            return {"error": "The submission URL must start with http:// or https://"}

        if payload.get("url") and not payload["url"].startswith("http"):
            return {
                "error": "The 'url' field in payload must be an absolute URL starting with http:// or https://"
            }

        logger.info(
            f"Submitting answer to: {post_endpoint_url} with payload: {payload}"
        )

        with httpx.Client(timeout=15.0) as client:
            response = client.post(post_endpoint_url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()

    except httpx.HTTPError as e:
        logger.error(f"Submission failed: {e}")
        return {"error": f"Submission failed: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"error": f"Unexpected error: {str(e)}"}
