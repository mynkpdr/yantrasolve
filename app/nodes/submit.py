"""Submit node for sending answers to the server."""

import json
from app.graph.state import QuizState
from app.utils.logging import logger
from langchain_core.messages import ToolMessage


async def submit_node(state: QuizState) -> QuizState:
    """Execute submit_answer_tool and record result."""
    logger.info("Submitting answer")

    last_message = state["messages"][-1]
    submit_tool_call = last_message.tool_calls[-1]

    # Find and invoke the submit tool
    tool = next(t for t in state["tools"] if t.name == submit_tool_call["name"])
    observation = await tool.ainvoke(submit_tool_call["args"])

    logger.debug(f"Submission response: {json.dumps(observation, indent=2)}")

    return {
        "submission_result": observation,
        "answer_payload": submit_tool_call["args"].get("payload", {}),
        "messages": [
            ToolMessage(content=str(observation), tool_call_id=submit_tool_call["id"])
        ],
        "submitted_answers": state.get("submitted_answers", [])
        + [submit_tool_call["args"]],
    }
