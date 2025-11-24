from app.utils.logging import logger
from app.graph.state import QuizState


async def fetch_context_node(state: QuizState) -> QuizState:
    # Implementation of fetching context from the URL
    # TODO: Add actual fetching logic here
    logger.info(state)
    return state
