"""Tests for app/graph/state.py"""

from app.graph.state import QuizState


class TestQuizState:
    """Test cases for QuizState TypedDict."""

    def test_quiz_state_is_typed_dict(self):
        """Test that QuizState is a TypedDict."""
        # QuizState should be a TypedDict subclass
        assert hasattr(QuizState, "__annotations__")

    def test_quiz_state_has_required_fields(self):
        """Test that QuizState contains all required fields."""
        annotations = QuizState.__annotations__

        required_fields = [
            "email",
            "secret",
            "current_url",
            "answer_payload",
            "start_time",
            "is_complete",
            "completed_quizzes",
            "submission_result",
            "submitted_answers",
            "html",
            "text",
            "console_logs",
            "screenshot_path",
            "tools",
            "attempt_count",
            "messages",
            "resources",
        ]

        for field in required_fields:
            assert field in annotations, f"Missing field: {field}"

    def test_quiz_state_field_types(self):
        """Test that QuizState fields have correct type annotations."""
        annotations = QuizState.__annotations__

        # Check key field types
        assert annotations["email"] is str
        assert annotations["secret"] is str
        assert annotations["current_url"] is str
        assert annotations["start_time"] is float
        assert annotations["is_complete"] is bool
        assert annotations["attempt_count"] is int
        assert annotations["html"] is str
        assert annotations["text"] is str
        assert annotations["screenshot_path"] is str

    def test_quiz_state_can_be_instantiated(self):
        """Test that QuizState can be used as a dictionary."""
        from unittest.mock import MagicMock

        state: QuizState = {
            "email": "test@example.com",
            "secret": "test-secret",
            "current_url": "http://example.com",
            "answer_payload": None,
            "start_time": 0.0,
            "is_complete": False,
            "completed_quizzes": [],
            "submission_result": {},
            "submitted_answers": [],
            "html": "",
            "text": "",
            "console_logs": [],
            "screenshot_path": "",
            "tools": [],
            "attempt_count": 0,
            "messages": [],
            "resources": MagicMock(),
        }

        assert state["email"] == "test@example.com"
        assert state["is_complete"] is False
        assert state["attempt_count"] == 0
