from app.utils.logging import logger
from app.graph.state import QuizState
from langchain_core.messages import ToolMessage
import asyncio


async def tool_execution_node(state: QuizState) -> dict:
    """Execute tool calls with robust error handling."""
    logger.info(f"\n{'#' * 30}\n3. Executing tools...\n{'#' * 30}")
    messages = state["messages"]
    last_message = messages[-1]

    # Handle case where there are no tool calls
    tool_calls = getattr(last_message, "tool_calls", None)
    if not tool_calls:
        logger.warning("No tool calls found in last message")
        return {"messages": []}

    result = []
    for tool_call in tool_calls:
        tool_name = tool_call.get("name", "unknown")
        tool_id = tool_call.get("id", "unknown")
        
        try:
            # Find the tool
            tool = next((t for t in state["tools"] if t.name == tool_name), None)
            
            if not tool:
                logger.error(f"Tool not found: {tool_name}")
                result.append(
                    ToolMessage(content=f"Error: Tool '{tool_name}' not found", tool_call_id=tool_id)
                )
                continue
            
            # Execute with timeout
            try:
                observation = await asyncio.wait_for(
                    tool.ainvoke(tool_call["args"]),
                    timeout=120  # 2 minute timeout per tool
                )
            except asyncio.TimeoutError:
                observation = f"Tool '{tool_name}' timed out after 120 seconds"
                logger.error(observation)
            
            result.append(
                ToolMessage(content=str(observation), tool_call_id=tool_id)
            )
            
        except Exception as e:
            error_msg = f"Error executing {tool_name}: {str(e)}"
            logger.error(error_msg)
            result.append(
                ToolMessage(content=error_msg, tool_call_id=tool_id)
            )

    logger.info(f"Tool results: {len(result)} messages")
    return {"messages": result}
