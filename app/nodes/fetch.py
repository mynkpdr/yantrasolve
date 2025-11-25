from app.utils.logging import logger
from app.graph.state import QuizState


async def fetch_context_node(state: QuizState) -> QuizState:
    # Implementation of fetching context from the URL
    # TODO: Add actual fetching logic here
    logger.info(f"\n{'#' * 30}\n1. Fetching context from URL...\n{'#' * 30}")
    return state
