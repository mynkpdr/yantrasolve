from app.utils.logging import logger
from app.graph.state import QuizState


async def agent_node(state: QuizState) -> QuizState:
    # Implementation of the agent reasoning process
    # TODO: Add actual agent logic here
    logger.info(f"\n{'#' * 30}\n2. Agent reasoning process...\n{'#' * 30}")
    return state
