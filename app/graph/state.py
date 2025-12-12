"""LangGraph workflow state definition."""

from typing import Any, Dict, List, Sequence, Annotated
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langchain_core.tools import BaseTool
from langgraph.graph.message import add_messages
from app.graph.resources import GlobalResources


class QuizState(TypedDict):
    """State flowing through the LangGraph workflow."""

    # Input
    email: str
    secret: str
    current_url: str

    # Workflow state
    answer_payload: Any
    start_time: float
    is_complete: bool
    completed_quizzes: List[Dict[str, Any]]
    submission_result: Dict[str, Any]
    submitted_answers: List[Dict[str, Any]]

    # Page data
    html: str
    text: str
    console_logs: List[str]
    screenshot_path: str

    # Tools & messages
    tools: List[BaseTool]
    attempt_count: int
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # Resources
    resources: GlobalResources
