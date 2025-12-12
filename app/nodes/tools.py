"""Tool execution node for running agent tool calls."""

import asyncio
from app.config.settings import settings
from app.graph.state import QuizState
from app.utils.logging import logger
from langchain_core.messages import ToolMessage


async def tool_execution_node(state: QuizState) -> dict:
    """Execute tool calls with timeout and error handling."""
    last_message = state["messages"][-1]
    tool_calls = getattr(last_message, "tool_calls", None)
    logger.info(f"Executing tool calls (count={len(tool_calls or [])})")
    if not tool_calls:
        logger.warning("No tool calls found in last message")
        return {"messages": []}

    result = []
    for tc in tool_calls:
        tool_name, tool_id = tc.get("name", "unknown"), tc.get("id", "unknown")

        try:
            tool = next((t for t in state["tools"] if t.name == tool_name), None)
            if not tool:
                logger.error(f"Tool not found: {tool_name}")
                result.append(
                    ToolMessage(
                        content=f"Error: Tool '{tool_name}' not found",
                        tool_call_id=tool_id,
                    )
                )
                continue

            # Execute with timeout
            try:
                logger.debug(f"Invoking tool '{tool_name}' with args: {tc['args']}")
                observation = await asyncio.wait_for(
                    tool.ainvoke(tc["args"]), timeout=settings.TOOL_TIMEOUT
                )
                logger.debug(f"Tool '{tool_name}' result: {observation}")
            except asyncio.TimeoutError:
                observation = f"Tool '{tool_name}' timed out after {settings.TOOL_TIMEOUT} seconds"
                logger.error(observation)

            result.append(ToolMessage(content=str(observation), tool_call_id=tool_id))

        except Exception as e:
            error_msg = f"Error executing {tool_name}: {str(e)}"
            logger.error(error_msg)
            result.append(ToolMessage(content=error_msg, tool_call_id=tool_id))

    logger.info(f"Tool results: {len(result)} messages")
    return {"messages": result}
