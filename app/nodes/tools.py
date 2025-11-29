from app.utils.logging import logger
from app.graph.state import QuizState
from langchain_core.messages import ToolMessage


async def tool_execution_node(state: QuizState) -> dict:
    # Implementation of tool execution logic
    logger.info(f"\n{'#' * 30}\n3. Executing tools...\n{'#' * 30}")
    messages = state["messages"]
    last_message = messages[-1]

    result = []
    for tool_call in last_message.tool_calls:
        tool = next(t for t in state["tools"] if t.name == tool_call["name"])
        observation = await tool.ainvoke(tool_call["args"])
        result.append(
            ToolMessage(content=str(observation), tool_call_id=tool_call["id"])
        )
    logger.info(result)
    return {"messages": result}
