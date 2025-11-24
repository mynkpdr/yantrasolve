from typing import TypedDict, List


class QuizState(TypedDict):
    """
    State that flows through the LangGraph workflow.
    """

    # Input - Initial request data
    email: str
    secret: str
    current_url: str
    completed_urls: List[str]
