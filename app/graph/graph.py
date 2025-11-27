from langgraph.graph import StateGraph, END

from app.graph.state import QuizState
from app.nodes.fetch import fetch_context_node
from app.nodes.feedback import feedback_node
from app.nodes.agent import agent_node
from app.nodes.tools import tool_execution_node
from app.nodes.submit import submit_node


def route_agent_decision(state: QuizState) -> str:
    """
    Determines the next node based on the Agent's last message.

    Logic:
    1. If there are any tool calls:
        a. If any tool call is `submit_answer`, route to `submit_answer`
        b. Otherwise, route to `execute_tools`
    2. If there are no tool calls, stay in agent reasoning (optional) or END
    """
    last_message = state["messages"][-1]

    tool_calls = getattr(last_message, "tool_calls", [])

    if not tool_calls:
        # No tools called
        print(" No tool calls made by agent.")
        # TODO: Implement this later: for now, we route to execute_tools to avoid stalling
        return "execute_tools"

    # Check if any tool call is submit_answer
    for tc in tool_calls:
        name = tc["name"]
        if name == "submit_answer_tool":
            return "submit_answer"

    # Otherwise, execute all other tools
    return "execute_tools"


def route_feedback(state):
    """
    Determines the next node based on the server feedback after submission.
    Routes:
        - fetch_context: if there's a next URL to fetch
        - END: if quiz is complete or no next URL
    """
    # TODO: Implement actual routing logic based on state analysis
    result = state["submission_result"]

    if state.get("is_complete"):
        return END

    if result.get("correct"):
        # If correct and new URL exists -> Loop back to start
        return "fetch_context"

    # If incorrect, checking if we have time/attempts left
    if state["attempt_count"] < 5:  # Limit retries
        return "fetch_context"

    # If simply moving to next quiz (skip) or giving up
    if result.get("url"):
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
        {"execute_tools": "execute_tools", "submit_answer": "submit_answer"},
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
            END: END,
        },
    )

    return workflow.compile()
