"""LangGraph workflow for quiz solving."""

import time
from langgraph.graph import StateGraph, END
from app.config.settings import settings
from app.graph.state import QuizState
from app.nodes.fetch import fetch_context_node
from app.nodes.feedback import feedback_node
from app.nodes.agent import agent_node
from app.nodes.tools import tool_execution_node
from app.nodes.submit import submit_node
from app.utils.logging import logger


def route_agent_decision(state: QuizState) -> str:
    """Route based on agent's tool calls. Returns next node name."""
    last_message = state["messages"][-1]
    elapsed = time.time() - state.get("start_time", time.time())

    if elapsed > settings.QUIZ_TIMEOUT_SECONDS:
        logger.warning(
            f"Quiz timeout ({elapsed:.0f}s > {settings.QUIZ_TIMEOUT_SECONDS}s)"
        )

    tool_calls = getattr(last_message, "tool_calls", None) or []
    if not tool_calls:
        logger.info("No tool calls, looping back to agent")
        return "agent_reasoning"

    # Check for submit_answer tool
    for tc in tool_calls:
        if tc.get("name") == "submit_answer_tool":
            return "submit_answer"
    return "execute_tools"


def route_feedback(state: QuizState) -> str:
    """Route based on submission feedback. Handles correct/incorrect/timeout."""
    result = state.get("submission_result", {})
    elapsed = time.time() - state.get("start_time", time.time())
    is_timeout = elapsed > settings.QUIZ_TIMEOUT_SECONDS

    if state.get("is_complete"):
        return END

    if result.get("correct"):
        return "fetch_context"

    # Incorrect: retry if time/attempts remain
    attempt_count = state.get("attempt_count", 0)
    if not is_timeout and attempt_count < 10:
        return "agent_reasoning"

    # Timeout or max attempts: move to next quiz or end
    if result.get("url"):
        logger.warning(
            f"Moving to next quiz after {attempt_count} attempts / {elapsed:.0f}s"
        )
        return "fetch_context"
    return END


def create_quiz_graph() -> StateGraph:
    """Build and compile the quiz-solving workflow graph."""
    workflow = StateGraph(QuizState)

    # Add nodes
    workflow.add_node("fetch_context", fetch_context_node)
    workflow.add_node("agent_reasoning", agent_node)
    workflow.add_node("execute_tools", tool_execution_node)
    workflow.add_node("submit_answer", submit_node)
    workflow.add_node("process_feedback", feedback_node)

    # Define flow
    workflow.set_entry_point("fetch_context")
    workflow.add_edge("fetch_context", "agent_reasoning")
    workflow.add_conditional_edges(
        "agent_reasoning",
        route_agent_decision,
        {
            "execute_tools": "execute_tools",
            "submit_answer": "submit_answer",
            "agent_reasoning": "agent_reasoning",
        },
    )
    workflow.add_edge("execute_tools", "agent_reasoning")
    workflow.add_edge("submit_answer", "process_feedback")
    workflow.add_conditional_edges(
        "process_feedback",
        route_feedback,
        {
            "fetch_context": "fetch_context",
            "agent_reasoning": "agent_reasoning",
            END: END,
        },
    )

    return workflow.compile()
