from app.utils.logging import logger
from app.graph.state import QuizState


async def submit_node(state: QuizState) -> QuizState:
    # Implementation of submitting answers to the server
    # TODO: Add actual submission logic here
    logger.info(f"\n{'#' * 30}\n4. Submitting answers to server...\n{'#' * 30}")
    return state
