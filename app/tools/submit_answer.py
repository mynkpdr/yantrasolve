"""Quiz answer submission tool."""

import json
from typing import Dict, Any
import httpx
from langchain_core.tools import tool
from app.utils.logging import logger


@tool
def submit_answer_tool(post_endpoint_url: str, payload: Dict[str, Any]) -> dict:
    """Submit quiz answer payload via HTTP POST.

    Args:
        post_endpoint_url: Submission URL (must start with http:// or https://)
        payload: JSON payload with email, secret, url, and answer

    Returns:
        Server response as dict or error message
    """
    # Validate URLs
    if not post_endpoint_url.startswith("http"):
        return {"error": "The submission URL must start with http:// or https://"}
    if payload.get("url") and not payload["url"].startswith("http"):
        return {"error": "The 'url' field in payload must be an absolute URL"}

    try:
        logger.info(
            f"\nPOST: {post_endpoint_url} with payload: {json.dumps(payload, indent=2)}"
        )
        with httpx.Client(timeout=15.0) as client:
            response = client.post(
                post_endpoint_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Submission failed: {e}")
        return {"error": f"Submission failed: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"error": f"Unexpected error: {str(e)}"}
