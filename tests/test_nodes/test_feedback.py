"""Tests for app/nodes/feedback.py"""

import time
from unittest.mock import MagicMock

import pytest
from langchain_core.messages import HumanMessage

from app.nodes.feedback import feedback_node


class TestFeedbackNode:
    """Test cases for feedback_node function."""

    @pytest.fixture
    def base_state(self):
        """Create a base state for testing."""
        mock_message = MagicMock()
        mock_message.id = "msg-1"

        return {
            "current_url": "http://example.com/quiz",
            "answer_payload": {"answer": "42"},
            "start_time": time.time(),
            "completed_quizzes": [],
            "messages": [mock_message],
            "submission_result": {},
            "submitted_answers": [],
        }

    @pytest.mark.asyncio
    async def test_correct_answer_with_next_url(self, base_state, mocker):
        """Test handling of correct answer with next URL."""
        mocker.patch("app.nodes.feedback.reset_python_session")

        base_state["submission_result"] = {
            "correct": True,
            "url": "http://example.com/next-quiz",
        }

        result = await feedback_node(base_state)

        assert result["current_url"] == "http://example.com/next-quiz"
        assert result["attempt_count"] == 0
        assert result["is_complete"] is False
        assert len(result["completed_quizzes"]) == 1
        assert result["submitted_answers"] == []

    @pytest.mark.asyncio
    async def test_correct_answer_without_next_url(self, base_state):
        """Test handling of correct answer without next URL (quiz complete)."""
        base_state["submission_result"] = {
            "correct": True,
            "url": None,
        }

        result = await feedback_node(base_state)

        assert result["is_complete"] is True
        assert len(result["completed_quizzes"]) == 1

    @pytest.mark.asyncio
    async def test_incorrect_answer_with_time_remaining(self, base_state, mocker):
        """Test handling of incorrect answer when time remains."""
        mocker.patch("app.nodes.feedback.settings.QUIZ_TIMEOUT_SECONDS", 180)

        base_state["submission_result"] = {
            "correct": False,
            "reason": "Incorrect value",
            "url": "http://example.com/next",
        }
        base_state["attempt_count"] = 2

        result = await feedback_node(base_state)

        assert result["attempt_count"] == 3
        assert "messages" in result
        # Should include feedback message
        feedback_messages = [
            m for m in result["messages"] if isinstance(m, HumanMessage)
        ]
        assert len(feedback_messages) > 0

    @pytest.mark.asyncio
    async def test_incorrect_answer_timeout_with_next_url(self, base_state, mocker):
        """Test handling of incorrect answer on timeout with next URL."""
        mocker.patch("app.nodes.feedback.settings.QUIZ_TIMEOUT_SECONDS", 1)
        mocker.patch("app.nodes.feedback.reset_python_session")

        base_state["start_time"] = time.time() - 100  # Started 100 seconds ago
        base_state["submission_result"] = {
            "correct": False,
            "reason": "Wrong answer",
            "url": "http://example.com/next-quiz",
        }
        base_state["attempt_count"] = 5

        result = await feedback_node(base_state)

        assert result["current_url"] == "http://example.com/next-quiz"
        assert result["attempt_count"] == 0
        assert result["is_complete"] is False

    @pytest.mark.asyncio
    async def test_incorrect_answer_timeout_without_next_url(self, base_state, mocker):
        """Test handling of incorrect answer on timeout without next URL."""
        mocker.patch("app.nodes.feedback.settings.QUIZ_TIMEOUT_SECONDS", 1)

        base_state["start_time"] = time.time() - 100  # Started 100 seconds ago
        base_state["submission_result"] = {
            "correct": False,
            "reason": "Wrong answer",
            "url": None,
        }
        base_state["attempt_count"] = 5

        result = await feedback_node(base_state)

        assert result["is_complete"] is True

    @pytest.mark.asyncio
    async def test_feedback_message_includes_reason(self, base_state, mocker):
        """Test that feedback message includes the server's reason."""
        mocker.patch("app.nodes.feedback.settings.QUIZ_TIMEOUT_SECONDS", 180)

        base_state["submission_result"] = {
            "correct": False,
            "reason": "Expected integer, got string",
            "url": "http://example.com/next",
        }

        result = await feedback_node(base_state)

        # Find the feedback message
        feedback_msgs = [m for m in result["messages"] if isinstance(m, HumanMessage)]
        assert len(feedback_msgs) > 0

        feedback_content = feedback_msgs[0].content
        assert "Expected integer, got string" in feedback_content

    @pytest.mark.asyncio
    async def test_attempt_count_incremented(self, base_state, mocker):
        """Test that attempt count is incremented on incorrect answer."""
        mocker.patch("app.nodes.feedback.settings.QUIZ_TIMEOUT_SECONDS", 180)

        base_state["submission_result"] = {"correct": False}
        base_state["attempt_count"] = 3

        result = await feedback_node(base_state)

        assert result["attempt_count"] == 4

    @pytest.mark.asyncio
    async def test_completed_quizzes_updated(self, base_state, mocker):
        """Test that completed_quizzes is updated on correct answer."""
        mocker.patch("app.nodes.feedback.reset_python_session")

        base_state["submission_result"] = {
            "correct": True,
            "url": "http://example.com/next",
        }
        base_state["completed_quizzes"] = [{"url": "http://example.com/old"}]

        result = await feedback_node(base_state)

        assert len(result["completed_quizzes"]) == 2
        assert result["completed_quizzes"][0]["url"] == "http://example.com/old"
        assert result["completed_quizzes"][1]["url"] == "http://example.com/quiz"

    @pytest.mark.asyncio
    async def test_context_reset_on_correct_answer(self, base_state, mocker):
        """Test that context is reset when moving to next quiz."""
        mocker.patch("app.nodes.feedback.reset_python_session")

        base_state["submission_result"] = {
            "correct": True,
            "url": "http://example.com/next",
        }
        base_state["html"] = "<html>old content</html>"
        base_state["text"] = "old text"
        base_state["screenshot_path"] = "/tmp/old_screenshot.png"

        result = await feedback_node(base_state)

        assert result["html"] == ""
        assert result["text"] == ""
        assert result["screenshot_path"] == ""
        assert result["console_logs"] == []
