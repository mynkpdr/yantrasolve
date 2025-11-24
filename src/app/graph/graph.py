from langgraph.graph import StateGraph, END

from app.graph.state import QuizState
from app.nodes.fetch import fetch_context_node


# Build the graph
def create_quiz_graph() -> StateGraph:
    workflow = StateGraph(QuizState)

    # 1. FETCH NODE
    workflow.add_node("fetch_context", fetch_context_node)

    # TODO: Add more nodes and edges for the quiz-solving process
    workflow.set_entry_point("fetch_context")
    workflow.add_edge("fetch_context", END)

    return workflow.compile()
