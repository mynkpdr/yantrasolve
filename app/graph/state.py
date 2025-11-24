from typing import TypedDict, List

from app.graph.resources import GlobalResources


class QuizState(TypedDict):
    """
    State that flows through the LangGraph workflow.
    """

    # Input - Initial request data
    email: str
    secret: str
    current_url: str

    resources: GlobalResources
    completed_urls: List[str]
