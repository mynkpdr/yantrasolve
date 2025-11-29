from typing import Any, Dict, TypedDict, List

from app.graph.resources import GlobalResources
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing import Sequence, Annotated
from langchain_core.tools import BaseTool


class QuizState(TypedDict):
    """
    State that flows through the LangGraph workflow.
    """

    # Input - Initial request data
    email: str
    secret: str
    current_url: str
    answer_payload: Any
    start_time: float
    is_complete: bool

    html: str
    text: str
    console_logs: List[str]
    screenshot_path: str

    tools: List[BaseTool]
    attempt_count: int
    messages: Annotated[Sequence[BaseMessage], add_messages]

    resources: GlobalResources
    completed_quizzes: List[Dict[str, Any]]
    submission_result: Dict[str, Any]
