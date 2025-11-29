from langgraph.graph import StateGraph, END

from app.graph.state import QuizState
from app.nodes.fetch import fetch_context_node
from app.nodes.feedback import feedback_node
from app.nodes.agent import agent_node
from app.nodes.tools import tool_execution_node
from app.nodes.submit import submit_node
from app.utils.logging import logger
import time


# 3 minutes per quiz timeout
QUIZ_TIMEOUT_SECONDS = 180


def route_agent_decision(state: QuizState) -> str:
    """
    Determines the next node based on the Agent's last message.
    Includes time-based forcing to submit if running out of time.
    """
    last_message = state["messages"][-1]
    
    # Check time - if running low, force continue trying
    elapsed = time.time() - state.get("start_time", time.time())
    if elapsed > QUIZ_TIMEOUT_SECONDS:
        logger.warning(f"Quiz timeout ({elapsed:.0f}s > {QUIZ_TIMEOUT_SECONDS}s)")
        # Time's up - but we don't stop, we let feedback handle moving to next
    
    tool_calls = getattr(last_message, "tool_calls", None) or []

    if not tool_calls:
        # No tools called - loop back to agent
        logger.info("No tool calls, looping back to agent")
        return "agent_reasoning"

    # Check if any tool call is submit_answer
    for tc in tool_calls:
        name = tc.get("name", "")
        if name == "submit_answer_tool":
            return "submit_answer"

    # Otherwise, execute all other tools
    return "execute_tools"


def route_feedback(state: QuizState) -> str:
    """
    Determines the next node based on the server feedback after submission.
    
    Time-based logic:
    - If correct: move to next URL
    - If incorrect but time remaining: retry (go back to agent)
    - If incorrect and time exceeded: move to next URL if available, else END
    """
    result = state.get("submission_result", {})
    elapsed = time.time() - state.get("start_time", time.time())
    is_timeout = elapsed > QUIZ_TIMEOUT_SECONDS

    if state.get("is_complete"):
        logger.info("Quiz complete!")
        return END

    logger.info(result)
    if result.get("correct"):
        logger.info("Answer correct! Moving to next quiz.")
        return "fetch_context"

    # Incorrect answer
    attempt_count = state.get("attempt_count", 0)
    
    if not is_timeout and attempt_count < 10:
        # Still have time - retry by going back to agent
        logger.info(f"Incorrect (attempt {attempt_count}), {QUIZ_TIMEOUT_SECONDS - elapsed:.0f}s remaining, retrying...")
        return "agent_reasoning"
    
    # Time's up or too many attempts - move to next quiz
    if result.get("url"):
        logger.warning(f"Moving to next quiz after {attempt_count} attempts / {elapsed:.0f}s")
        return "fetch_context"

    return END


# Build the graph
def create_quiz_graph() -> StateGraph:
    workflow = StateGraph(QuizState)

    # 1. FETCH NODE
    workflow.add_node("fetch_context", fetch_context_node)

    # 2. AGENT NODE
    workflow.add_node("agent_reasoning", agent_node)

    # 3. TOOLS NODE: Executes any tool calls made by the agent
    workflow.add_node("execute_tools", tool_execution_node)

    # 4. SUBMIT NODE: Sends the POST request to the server
    workflow.add_node("submit_answer", submit_node)

    # 5. PARSER NODE: Reads the server JSON response (Correct/Incorrect/Next URL etc.)
    workflow.add_node("process_feedback", feedback_node)

    # --- EDGES / FLOW LOGIC ---
    # Start by fetching data
    workflow.set_entry_point("fetch_context")
    workflow.add_edge("fetch_context", "agent_reasoning")

    # Conditional Edge: Decide based on Agent's tool calls
    workflow.add_conditional_edges(
        "agent_reasoning",
        route_agent_decision,
        {
            "execute_tools": "execute_tools",
            "submit_answer": "submit_answer",
            "agent_reasoning": "agent_reasoning",  # Loop back if no tool calls
        },
    )

    # After tools, always go back to agent to analyze tool output
    workflow.add_edge("execute_tools", "agent_reasoning")

    # After submission, process the result
    workflow.add_edge("submit_answer", "process_feedback")

    # Conditional Edge: Decide based on server feedback
    workflow.add_conditional_edges(
        "process_feedback",
        route_feedback,
        {
            "fetch_context": "fetch_context",
            "agent_reasoning": "agent_reasoning",  # Retry on incorrect answer
            END: END,
        },
    )

    return workflow.compile()
