from app.utils.logging import logger
from app.graph.state import QuizState


async def submit_node(state: QuizState) -> QuizState:
    # Implementation of submitting answers to the server
    logger.info(f"\n{'#' * 30}\n4. Submitting answers to server...\n{'#' * 30}")
    messages = state["messages"]
    last_message = messages[-1]

    submit_tool_call = last_message.tool_calls[-1]
    tool = next(t for t in state["tools"] if t.name == submit_tool_call["name"])
    observation = await tool.ainvoke(submit_tool_call["args"])
    logger.info(f"Submission observation: {observation}")

    # return {
    #     "submission_result": ToolMessage(content=observation, tool_call_id=submit_tool_call["id"])
    # }
    return {
        "submission_result": observation,
        "answer_payload": submit_tool_call["args"].get("payload", {}),
    }
