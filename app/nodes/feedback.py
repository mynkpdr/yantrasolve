from app.utils.logging import logger
from app.graph.state import QuizState


async def feedback_node(state: QuizState) -> QuizState:
    # Implementation of processing feedback from submission result
    # TODO: Add actual feedback processing logic here
    logger.info(
        f"\n{'#' * 30}\n5. Processing feedback from submission result...\n{'#' * 30}"
    )
    return state
